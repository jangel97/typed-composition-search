from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    """Multiple input_types are treated as OR (reachable from any), not AND (all required)."""

    name: str
    input_types: tuple[str, ...]
    output_types: tuple[str, ...]
    description: str = ""
