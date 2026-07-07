"""Export graph snapshot for Stripe: entity types + typed tool edges.

Creates graph_snapshot.json in the same format as aap_mcp for use with
training data generation and encoder training.
"""

import json
from pathlib import Path

from .openapi_parser import parse_spec, collect_entity_types
from .registry import DEFAULT_SPEC

HERE = Path(__file__).resolve().parent


def generate_snapshot(spec_path=DEFAULT_SPEC):
    ops = parse_spec(spec_path)
    entity_types = collect_entity_types(ops)
    entity_types["Platform"] = "The Stripe platform root (starting point for listing resources)"

    tools = []
    for op in ops:
        tools.append({
            "name": op.full_name,
            "input_types": list(op.input_types),
            "output_types": list(op.output_types),
            "description": op.description,
        })

    snapshot = {
        "entity_types": entity_types,
        "tools": tools,
        "stats": {
            "total_tools": len(tools),
            "entity_type_count": len(entity_types),
        },
    }

    out = HERE / "graph_snapshot.json"
    with open(out, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"Saved {out}")
    print(f"  Tools: {len(tools)}")
    print(f"  Entity types: {len(entity_types)}")

    return snapshot


if __name__ == "__main__":
    generate_snapshot()
