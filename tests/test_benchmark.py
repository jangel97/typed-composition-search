from benchmarks.devops_queries import QUERIES
from benchmarks.devops_registry import build_devops_registry


def _registry():
    return build_devops_registry()


class TestRecall:
    def test_all_required_tools_found(self):
        r = _registry()
        for q in QUERIES:
            relevant = r.relevant_tools(q.initial, q.goal)
            returned_names = {t.name for t in relevant}
            missing = q.required_tools - returned_names
            assert not missing, (
                f"{q.name}: missing required tools {missing}"
            )

    def test_recall_is_100_percent(self):
        r = _registry()
        for q in QUERIES:
            relevant = r.relevant_tools(q.initial, q.goal)
            returned_names = {t.name for t in relevant}
            recall = len(q.required_tools & returned_names) / len(q.required_tools)
            assert recall == 1.0, f"{q.name}: recall = {recall:.0%}"


class TestPlanCorrectness:
    def test_all_queries_have_plans(self):
        r = _registry()
        for q in QUERIES:
            plan = r.plan(q.initial, q.goal)
            assert plan is not None, f"{q.name}: no plan found"

    def test_plans_are_executable(self):
        r = _registry()
        for q in QUERIES:
            plan = r.plan(q.initial, q.goal)
            assert plan is not None
            available = set(q.initial)
            for tool in plan:
                assert tool.inputs <= available, (
                    f"{q.name}: {tool.name} needs {tool.inputs - available}"
                )
                available |= tool.outputs
            assert q.goal <= available, f"{q.name}: goal not satisfied"


class TestPruning:
    def test_relevant_tools_is_subset_of_all(self):
        r = _registry()
        all_tools = set(r._tools)
        for q in QUERIES:
            relevant = r.relevant_tools(q.initial, q.goal)
            assert relevant <= all_tools

    def test_plan_tools_are_subset_of_relevant(self):
        r = _registry()
        for q in QUERIES:
            relevant = r.relevant_tools(q.initial, q.goal)
            plan = r.plan(q.initial, q.goal)
            assert plan is not None
            assert set(plan) <= relevant, (
                f"{q.name}: plan contains tools not in relevant set"
            )

    def test_pruning_ratio_above_threshold(self):
        r = _registry()
        total = len(r._tools)
        for q in QUERIES:
            relevant = r.relevant_tools(q.initial, q.goal)
            pruning = 1 - len(relevant) / total
            assert pruning >= 0.50, (
                f"{q.name}: pruning {pruning:.0%} below 50% threshold"
            )
