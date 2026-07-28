"""TCS registry built from real AAP MCP Server OpenAPI specs."""

from __future__ import annotations

import re
from pathlib import Path

from typed_composition_search import Registry

from .openapi_parser import collect_entity_types, parse_all_specs

DATA_DIR = Path.home() / "aap-mcp-server" / "data"


def _to_snake(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def build_registry(
    services: list[str] | None = None,
    data_dir: Path | str = DATA_DIR,
) -> Registry:
    """Build a TCS Registry from the AAP MCP Server OpenAPI specs.

    Args:
        services: Optional filter to specific services (controller, eda, galaxy, gateway).
        data_dir: Path to the directory containing the JSON spec files.
    """
    ops = parse_all_specs(data_dir, services=services)

    reg = Registry()

    for op in ops:
        reg.register(
            op.full_name,
            op.input_types,
            op.output_types,
            op.description,
        )

    return reg


def _build_entity_types(
    services: list[str] | None = None,
    data_dir: Path | str = DATA_DIR,
) -> dict[str, str]:
    ops = parse_all_specs(data_dir, services=services)
    all_types = collect_entity_types(ops)

    # Only include core types for LLM prompting — List/Name/Spec are structural
    core: dict[str, str] = {}
    for name, desc in sorted(all_types.items()):
        if name.endswith(("List", "Name", "Spec")):
            continue
        core[name] = desc

    core["Platform"] = "The automation platform root (starting point for listing resources)"
    return core


ENTITY_TYPES = _build_entity_types()


def freeze_graph(output_path: str | Path) -> None:
    """Export the graph as a JSON snapshot for reproducibility and TS integration."""
    import json

    reg = build_registry()
    tools = [
        {
            "name": t.name,
            "input_types": list(t.input_types),
            "output_types": list(t.output_types),
            "description": t.description,
        }
        for t in reg._tools
    ]
    snapshot = {
        "entity_types": ENTITY_TYPES,
        "tools": tools,
        "stats": {
            "total_tools": len(tools),
            "entity_type_count": len(ENTITY_TYPES),
        },
    }
    output_path = Path(output_path)
    output_path.write_text(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "freeze":
        out = sys.argv[2] if len(sys.argv) > 2 else "benchmarks/aap_mcp/graph_snapshot.json"
        freeze_graph(out)
        print(f"Graph frozen to {out}")
    else:
        reg = build_registry()
        print(f"Tools: {len(reg._tools)}")
        print(f"Entity types: {len(ENTITY_TYPES)}")
        for name, desc in sorted(ENTITY_TYPES.items()):
            print(f"  {name}: {desc}")
