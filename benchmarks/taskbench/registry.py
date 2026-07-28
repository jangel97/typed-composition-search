"""TaskBench registry — builds typed composition graphs from TaskBench tool definitions.

TaskBench uses coarse modality types (text, image, audio, video). Many tools share
the same type signature (e.g., Translation and Summarization are both text→text),
so the graph cannot disambiguate between them by type alone. This is by design:
it tests the limits of type-based routing on a coarse type system.
"""

import json
from pathlib import Path

from typed_composition_search import Registry

DATA_DIR = Path(__file__).parent / "data"

ENTITY_TYPES = {
    "text": "Text content — natural language, labels, descriptions, or transcriptions",
    "image": "Image data — photographs, generated images, or visual content",
    "audio": "Audio data — speech, music, or sound",
    "video": "Video data — recorded or generated video content",
}


def _load_tools(filename: str) -> list[dict]:
    with open(DATA_DIR / filename) as f:
        data = json.load(f)
    return data["nodes"]


def build_registry(domain: str = "huggingface") -> Registry:
    filename = "hf_tools.json" if domain == "huggingface" else "mm_tools.json"
    tools = _load_tools(filename)
    reg = Registry()
    for tool in tools:
        input_types = tuple(tool["input-type"]) if tool["input-type"] else ()
        output_types = tuple(tool["output-type"]) if tool["output-type"] else ()
        if not input_types or not output_types:
            continue
        reg.register(
            name=tool["id"],
            input_types=input_types,
            output_types=output_types,
            description=tool["desc"],
        )
    return reg


def build_registry_huggingface() -> Registry:
    return build_registry("huggingface")


def build_registry_multimedia() -> Registry:
    return build_registry("multimedia")
