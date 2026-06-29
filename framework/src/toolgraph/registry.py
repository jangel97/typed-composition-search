from .graph import Graph, Path
from .tool import Tool


class Registry:
    def __init__(self) -> None:
        self._graph = Graph()
        self._tools: list[Tool] = []
        self._entity_types: dict[str, str] = {}

    def register(
        self,
        name: str,
        input_types: tuple[str, ...],
        output_types: tuple[str, ...],
        description: str = "",
    ) -> Tool:
        tool = Tool(
            name=name,
            input_types=input_types,
            output_types=output_types,
            description=description,
        )
        self._tools.append(tool)
        self._graph.add_tool(tool)
        return tool

    def resolve(self, source_type: str, target_type: str) -> Path | None:
        return self._graph.find_path(source_type, target_type)

    def reachable_types(self, source_type: str) -> set[str]:
        return self._graph.reachable_types(source_type)

    def reverse_reachable_types(self, target_type: str) -> set[str]:
        return self._graph.reverse_reachable_types(target_type)

    def types(self) -> set[str]:
        return self._graph._all_nodes()

    @property
    def tools(self) -> list[Tool]:
        return list(self._tools)

    @property
    def graph(self) -> Graph:
        return self._graph

    @property
    def entity_types(self) -> dict[str, str]:
        return dict(self._entity_types)

    def set_entity_types(self, entity_types: dict[str, str]) -> None:
        self._entity_types = dict(entity_types)
