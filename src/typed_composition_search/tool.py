from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    name: str
    inputs: frozenset[str]
    outputs: frozenset[str]

    def __repr__(self) -> str:
        return f"Tool({self.name!r})"
