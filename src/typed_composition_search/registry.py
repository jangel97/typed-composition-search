from collections import deque
from collections.abc import Callable
from typing import Any

from .graph import CapabilityGraph
from .tool import Tool


class Registry:
    def __init__(self) -> None:
        self._tools: list[Tool] = []
        self._graph: CapabilityGraph | None = None

    def add_tool(self, name: str, inputs: list[str], outputs: list[str]) -> Tool:
        t = Tool(name=name, inputs=frozenset(inputs), outputs=frozenset(outputs))
        self._tools.append(t)
        self._graph = None
        return t

    def tool(
        self, inputs: list[str], outputs: list[str]
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.add_tool(fn.__name__, inputs, outputs)
            return fn

        return decorator

    def graph(self) -> CapabilityGraph:
        if self._graph is None:
            self._graph = CapabilityGraph(self._tools)
        return self._graph

    def relevant_tools(
        self,
        initial: set[str],
        goal: set[str],
        *,
        exclude_sources: bool = False,
        max_depth: int | None = None,
    ) -> set[Tool]:
        g = self.graph()
        _, forward_tools = g.forward_reachable(
            initial, exclude_sources=exclude_sources, max_depth=max_depth,
        )
        _, backward_tools = g.backward_reachable(goal, max_depth=max_depth)
        return forward_tools & backward_tools

    def plan(self, initial: set[str], goal: set[str]) -> list[Tool] | None:
        if goal <= initial:
            return []

        g = self.graph()
        relevant = self.relevant_tools(initial, goal)
        if not relevant:
            return None

        queue: deque[tuple[frozenset[str], list[Tool]]] = deque()
        queue.append((frozenset(initial), []))
        visited: set[frozenset[str]] = {frozenset(initial)}

        while queue:
            available, path = queue.popleft()

            for tool in relevant:
                if tool in path:
                    continue
                if not tool.inputs <= available:
                    continue

                new_available = available | tool.outputs
                new_path = path + [tool]

                if goal <= new_available:
                    return new_path

                if new_available not in visited:
                    visited.add(new_available)
                    queue.append((new_available, new_path))

        return None
