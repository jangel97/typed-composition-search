from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    name: str
    input_types: tuple[str, ...]
    output_types: tuple[str, ...]
    description: str = ""
