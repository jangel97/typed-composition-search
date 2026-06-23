from collections import deque
from dataclasses import dataclass
from typing import Any

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

    def _all_nodes(self) -> set[str]:
        nodes: set[str] = set()
        for t in self._edges:
            nodes.add(t)
        for t in self._reverse_edges:
            nodes.add(t)
        for tools in self._edges.values():
            for tool in tools:
                for out in tool.output_types:
                    nodes.add(out)
        return nodes

    def _directed_edges(self) -> list[tuple[str, str, str]]:
        seen: set[tuple[str, str, str]] = set()
        edges: list[tuple[str, str, str]] = []
        for tools in self._edges.values():
            for tool in tools:
                for inp in tool.input_types:
                    for out in tool.output_types:
                        key = (inp, out, tool.name)
                        if key not in seen:
                            seen.add(key)
                            edges.append(key)
        return edges

    def _bfs_shortest_path_length(self, source: str, target: str) -> int | None:
        if source == target:
            return 0
        visited: set[str] = {source}
        queue: deque[tuple[str, int]] = deque([(source, 0)])
        while queue:
            current, dist = queue.popleft()
            for tool in self._edges.get(current, []):
                for next_type in tool.output_types:
                    if next_type in visited:
                        continue
                    if next_type == target:
                        return dist + 1
                    visited.add(next_type)
                    queue.append((next_type, dist + 1))
        return None

    def metrics(self) -> dict[str, Any]:
        nodes = sorted(self._all_nodes())
        edges = self._directed_edges()
        n = len(nodes)

        # Degrees
        in_deg: dict[str, int] = {nd: 0 for nd in nodes}
        out_deg: dict[str, int] = {nd: 0 for nd in nodes}
        adj: dict[str, set[str]] = {nd: set() for nd in nodes}
        for src, tgt, _ in edges:
            out_deg[src] += 1
            in_deg[tgt] += 1
            adj.setdefault(src, set()).add(tgt)
            adj.setdefault(tgt, set()).add(src)

        avg_in = sum(in_deg.values()) / n if n else 0
        avg_out = sum(out_deg.values()) / n if n else 0
        max_in = max(in_deg.values()) if n else 0
        max_out = max(out_deg.values()) if n else 0

        # Connected components (undirected)
        visited: set[str] = set()
        components = 0
        for nd in nodes:
            if nd in visited:
                continue
            components += 1
            stack = [nd]
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                for neighbor in adj.get(cur, set()):
                    if neighbor not in visited:
                        stack.append(neighbor)

        # Branching factor (out-degree of nodes that have outgoing edges)
        branching_nodes = [d for d in out_deg.values() if d > 0]
        avg_branching = sum(branching_nodes) / len(branching_nodes) if branching_nodes else 0
        max_branching = max(branching_nodes) if branching_nodes else 0

        # All-pairs shortest paths (for reachability, diameter, betweenness)
        all_sp_lengths: list[int] = []
        reachable_pairs = 0
        total_pairs = n * (n - 1) if n > 1 else 1

        # BFS from every node, also compute betweenness
        betweenness: dict[str, float] = {nd: 0.0 for nd in nodes}
        for source in nodes:
            visited_bfs: set[str] = {source}
            queue_bfs: deque[tuple[str, int]] = deque([(source, 0)])
            predecessors: dict[str, list[str]] = {}
            distances: dict[str, int] = {source: 0}
            path_counts: dict[str, int] = {source: 1}
            order: list[str] = []

            while queue_bfs:
                current, dist = queue_bfs.popleft()
                order.append(current)
                for tool in self._edges.get(current, []):
                    for next_type in tool.output_types:
                        if next_type not in visited_bfs:
                            visited_bfs.add(next_type)
                            distances[next_type] = dist + 1
                            path_counts[next_type] = 0
                            predecessors[next_type] = []
                            queue_bfs.append((next_type, dist + 1))
                        if distances.get(next_type) == dist + 1:
                            path_counts[next_type] = path_counts.get(next_type, 0) + path_counts[current]
                            predecessors.setdefault(next_type, []).append(current)

            for target in visited_bfs:
                if target != source:
                    reachable_pairs += 1
                    all_sp_lengths.append(distances[target])

            # Accumulate betweenness (Brandes)
            dependency: dict[str, float] = {nd: 0.0 for nd in nodes}
            for w in reversed(order):
                for v in predecessors.get(w, []):
                    if path_counts[w] > 0:
                        dependency[v] += (path_counts[v] / path_counts[w]) * (1 + dependency[w])
                if w != source:
                    betweenness[w] += dependency[w]

        reachable_pct = round(100 * reachable_pairs / total_pairs, 1) if total_pairs else 0
        avg_sp = round(sum(all_sp_lengths) / len(all_sp_lengths), 2) if all_sp_lengths else 0
        diameter = max(all_sp_lengths) if all_sp_lengths else 0

        # Avg reachable sources/targets
        total_reachable_targets = sum(len(self.reachable_types(nd)) for nd in nodes)
        total_reachable_sources = sum(len(self.reverse_reachable_types(nd)) for nd in nodes)
        avg_reachable_targets = round(total_reachable_targets / n, 1) if n else 0
        avg_reachable_sources = round(total_reachable_sources / n, 1) if n else 0

        # Top betweenness
        top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
        top_betweenness = [{"type": t, "score": round(s, 2)} for t, s in top_betweenness if s > 0]

        # PageRank
        damping = 0.85
        pr: dict[str, float] = {nd: 1.0 / n for nd in nodes}
        out_neighbors: dict[str, list[str]] = {}
        for src, tgt, _ in edges:
            out_neighbors.setdefault(src, []).append(tgt)

        for _ in range(50):
            new_pr: dict[str, float] = {}
            for nd in nodes:
                rank = (1 - damping) / n
                for src in nodes:
                    if nd in out_neighbors.get(src, []):
                        out_count = len(out_neighbors[src])
                        rank += damping * pr[src] / out_count
                new_pr[nd] = rank
            pr = new_pr

        top_pagerank = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:5]
        top_pagerank = [{"type": t, "score": round(s, 4)} for t, s in top_pagerank]

        return {
            "structural": {
                "node_count": n,
                "edge_count": len(edges),
                "avg_in_degree": round(avg_in, 2),
                "avg_out_degree": round(avg_out, 2),
                "max_in_degree": max_in,
                "max_out_degree": max_out,
                "connected_components": components,
            },
            "reachability": {
                "reachable_pairs_pct": reachable_pct,
                "avg_shortest_path_length": avg_sp,
                "diameter": diameter,
                "avg_reachable_sources_per_target": avg_reachable_sources,
                "avg_reachable_targets_per_source": avg_reachable_targets,
            },
            "search_space": {
                "avg_branching_factor": round(avg_branching, 2),
                "max_branching_factor": max_branching,
            },
            "centrality": {
                "top_betweenness": top_betweenness,
                "top_pagerank": top_pagerank,
            },
        }

    def to_json(self) -> dict[str, Any]:
        nodes = [{"id": n} for n in sorted(self._all_nodes())]
        edges = [{"source": s, "target": t, "label": l} for s, t, l in self._directed_edges()]
        return {"nodes": nodes, "edges": edges}
