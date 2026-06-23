from collections import deque
from dataclasses import dataclass

from .tool import Tool


@dataclass(frozen=True)
class Path:
    types: list[str]
    tools: list[Tool]


class Graph:
    def __init__(self) -> None:
        self._edges: dict[str, list[Tool]] = {}
        self._reverse_edges: dict[str, list[Tool]] = {}

    def add_tool(self, tool: Tool) -> None:
        for input_type in tool.input_types:
            self._edges.setdefault(input_type, []).append(tool)
        for output_type in tool.output_types:
            self._reverse_edges.setdefault(output_type, []).append(tool)

    def find_path(self, source: str, target: str) -> Path | None:
        if source == target:
            return Path(types=[source], tools=[])

        visited: set[str] = {source}
        queue: deque[tuple[str, list[str], list[Tool]]] = deque()
        queue.append((source, [source], []))

        while queue:
            current, types, tools = queue.popleft()
            for tool in self._edges.get(current, []):
                for next_type in tool.output_types:
                    if next_type in visited:
                        continue
                    new_types = types + [next_type]
                    new_tools = tools + [tool]
                    if next_type == target:
                        return Path(types=new_types, tools=new_tools)
                    visited.add(next_type)
                    queue.append((next_type, new_types, new_tools))

        return None

    def reachable_types(self, source: str) -> set[str]:
        visited: set[str] = {source}
        queue: deque[str] = deque([source])
        while queue:
            current = queue.popleft()
            for tool in self._edges.get(current, []):
                for next_type in tool.output_types:
                    if next_type not in visited:
                        visited.add(next_type)
                        queue.append(next_type)
        visited.discard(source)
        return visited

    def reverse_reachable_types(self, target: str) -> set[str]:
        visited: set[str] = {target}
        queue: deque[str] = deque([target])
        while queue:
            current = queue.popleft()
            for tool in self._reverse_edges.get(current, []):
                for input_type in tool.input_types:
                    if input_type not in visited:
                        visited.add(input_type)
                        queue.append(input_type)
        visited.discard(target)
        return visited
