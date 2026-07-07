from .graph import Graph, Path
from .tool import Tool


class Registry:
    def __init__(self) -> None:
        self._graph = Graph()
        self._tools: list[Tool] = []

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

    def resolve(
        self, source_type: str, target_type: str, all_shortest: bool = False,
    ) -> Path | list[Path] | None:
        if all_shortest:
            return self._graph.find_all_shortest_paths(source_type, target_type)
        return self._graph.find_path(source_type, target_type)

    def resolve_candidates(self, source_type: str, target_type: str) -> set[str]:
        return self._graph.find_candidate_tools(source_type, target_type)

    def reachable_types(self, source_type: str) -> set[str]:
        return self._graph.reachable_types(source_type)

    def reverse_reachable_types(self, target_type: str) -> set[str]:
        return self._graph.reverse_reachable_types(target_type)
