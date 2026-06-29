import sys
from unittest.mock import MagicMock, patch

import pytest

from tcs import Registry
from tcs.predict import Prediction, TypePredictor, _parse_prediction


ENTITY_TYPES = {
    "Deployment": "A Kubernetes deployment",
    "Pod": "A running container",
    "PodLogs": "Logs from a pod",
}


def _mock_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    return resp


class TestParsePrediction:
    def test_valid_json(self):
        result = _parse_prediction('{"source_type": "Deployment", "target_type": "PodLogs"}')
        assert result == Prediction(source_type="Deployment", target_type="PodLogs")

    def test_json_embedded_in_text(self):
        text = 'Based on the query, I predict:\n{"source_type": "Deployment", "target_type": "PodLogs"}\nThis is because...'
        result = _parse_prediction(text)
        assert result == Prediction(source_type="Deployment", target_type="PodLogs")

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            _parse_prediction("I cannot determine the types")

    def test_missing_source_type_raises(self):
        with pytest.raises(ValueError, match="Missing source_type or target_type"):
            _parse_prediction('{"target_type": "Pod"}')

    def test_missing_target_type_raises(self):
        with pytest.raises(ValueError, match="Missing source_type or target_type"):
            _parse_prediction('{"source_type": "Deployment"}')

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            _parse_prediction("{source_type: broken}")


class TestTypePredictor:
    @patch("tcs.predict.TypePredictor.__init__", return_value=None)
    def _make_predictor(self, mock_init):
        predictor = TypePredictor.__new__(TypePredictor)
        predictor._model = "test-model"
        predictor._entity_types = ENTITY_TYPES
        predictor._litellm_kwargs = {}
        predictor._litellm = MagicMock()
        predictor._system_prompt = "test prompt"
        return predictor

    def test_predict_valid(self):
        predictor = self._make_predictor()
        predictor._litellm.completion.return_value = _mock_response(
            '{"source_type": "Deployment", "target_type": "PodLogs"}'
        )

        result = predictor.predict("get logs from nginx deployment")

        assert result == Prediction(source_type="Deployment", target_type="PodLogs")
        predictor._litellm.completion.assert_called_once()

    def test_predict_embedded_json(self):
        predictor = self._make_predictor()
        predictor._litellm.completion.return_value = _mock_response(
            'Here is my prediction:\n{"source_type": "Deployment", "target_type": "Pod"}\nDone.'
        )

        result = predictor.predict("list pods in deployment")

        assert result == Prediction(source_type="Deployment", target_type="Pod")

    def test_predict_invalid_json_raises(self):
        predictor = self._make_predictor()
        predictor._litellm.completion.return_value = _mock_response("no json here")

        with pytest.raises(ValueError, match="No JSON object found"):
            predictor.predict("some query")

    def test_resolve_returns_path(self):
        predictor = self._make_predictor()
        predictor._litellm.completion.return_value = _mock_response(
            '{"source_type": "Deployment", "target_type": "PodLogs"}'
        )

        reg = Registry()
        reg.register("get_pods", ("Deployment",), ("Pod",))
        reg.register("get_logs", ("Pod",), ("PodLogs",))

        path = predictor.resolve("get logs from nginx", reg)

        assert path is not None
        assert [t.name for t in path.tools] == ["get_pods", "get_logs"]
        assert path.types == ["Deployment", "Pod", "PodLogs"]

    def test_resolve_returns_none_when_no_path(self):
        predictor = self._make_predictor()
        predictor._litellm.completion.return_value = _mock_response(
            '{"source_type": "Deployment", "target_type": "UnknownType"}'
        )

        reg = Registry()
        reg.register("get_pods", ("Deployment",), ("Pod",))

        path = predictor.resolve("some impossible query", reg)

        assert path is None


class TestMissingLitellm:
    def test_import_error_without_litellm(self):
        with patch.dict(sys.modules, {"litellm": None}):
            with pytest.raises(ImportError, match="litellm is required"):
                TypePredictor(model="test", entity_types=ENTITY_TYPES)
