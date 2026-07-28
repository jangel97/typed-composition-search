"""Load TaskBench chain queries for benchmarking.

Extracts chain-type samples from TaskBench JSONL data and maps them
to the query format expected by run_benchmark.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _topological_order(nodes: list[dict], links: list[dict]) -> list[str] | None:
    tool_names = [n["task"] for n in nodes]
    targets = {l["target"] for l in links}
    link_map = {l["source"]: l["target"] for l in links}

    first = [t for t in tool_names if t not in targets]
    if not first:
        return None

    order = [first[0]]
    while order[-1] in link_map:
        order.append(link_map[order[-1]])
    return order if len(order) == len(tool_names) else None


def _parse_field(d: dict, key: str):
    val = d[key]
    return val if isinstance(val, list) else json.loads(val)


def load_queries(domain: str = "huggingface", max_queries: int | None = None) -> list[dict]:
    filename = "hf_data.json" if domain == "huggingface" else "mm_data.json"
    tool_types: dict[str, dict] = {}

    # Load tool type info
    tools_file = "hf_tools.json" if domain == "huggingface" else "mm_tools.json"
    with open(DATA_DIR / tools_file) as f:
        for node in json.load(f)["nodes"]:
            tool_types[node["id"]] = node

    queries = []
    with open(DATA_DIR / filename) as f:
        for line in f:
            d = json.loads(line)
            if d["type"] != "chain":
                continue

            nodes = _parse_field(d, "sampled_nodes")
            links = _parse_field(d, "sampled_links") if d.get("sampled_links") else _parse_field(d, "task_links")

            order = _topological_order(nodes, links)
            if not order:
                continue

            node_map = {n["task"]: n for n in nodes}
            first = node_map.get(order[0], {})
            last = node_map.get(order[-1], {})

            src_types = first.get("input-type", [])
            tgt_types = last.get("output-type", [])

            if not src_types or not tgt_types:
                continue

            source_type = src_types[0]
            target_type = tgt_types[0]

            queries.append({
                "id": f"tb_{d['id']}",
                "category": f"chain_{d['n_tools']}",
                "query": d["user_request"],
                "source_type": source_type,
                "target_type": target_type,
                "expected_tools": order,
            })

            if max_queries and len(queries) >= max_queries:
                break

    return queries


QUERIES_HF = load_queries("huggingface")
QUERIES_MM = load_queries("multimedia")
QUERIES = QUERIES_HF
