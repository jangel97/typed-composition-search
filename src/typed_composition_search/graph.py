from collections import deque

from .tool import Tool


class CapabilityGraph:
    def __init__(self, tools: list[Tool]) -> None:
        self.tools = tools
        self._consumers: dict[str, set[Tool]] = {}
        self._producers: dict[str, set[Tool]] = {}

        for tool in tools:
            for t in tool.inputs:
                self._consumers.setdefault(t, set()).add(tool)
            for t in tool.outputs:
                self._producers.setdefault(t, set()).add(tool)

    def forward_reachable(
        self,
        initial: set[str],
        *,
        exclude_sources: bool = False,
        max_depth: int | None = None,
    ) -> tuple[set[str], set[Tool]]:
        available = set(initial)
        fired: set[Tool] = set()
        depth = 0

        changed = True
        while changed:
            if max_depth is not None and depth >= max_depth:
                break
            changed = False
            for tool in self.tools:
                if tool in fired:
                    continue
                if exclude_sources and not tool.inputs:
                    continue
                if tool.inputs <= available:
                    available |= tool.outputs
                    fired.add(tool)
                    changed = True
            depth += 1

        return available, fired

    def backward_reachable(
        self,
        goal: set[str],
        *,
        max_depth: int | None = None,
    ) -> tuple[set[str], set[Tool]]:
        needed = set(goal)
        used: set[Tool] = set()
        queue: deque[tuple[str, int]] = deque((t, 0) for t in goal)

        while queue:
            t, depth = queue.popleft()
            if max_depth is not None and depth >= max_depth:
                continue
            for tool in self._producers.get(t, ()):
                if tool in used:
                    continue
                used.add(tool)
                for inp in tool.inputs:
                    if inp not in needed:
                        needed.add(inp)
                        queue.append((inp, depth + 1))

        return needed, used
