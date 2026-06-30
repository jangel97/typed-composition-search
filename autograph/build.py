"""Stage 3: Build a typed composition graph from semantic contracts and compatibility.

Each unique contract description (what a tool consumes or produces) becomes an
entity type node.  Compatibility judgments become graph edges: if tool A's output
is compatible with tool B's input, there is a path A_output → B_input.

When a tool's produce description exactly matches another tool's consume
description, the connection is direct (same node).  When compatibility holds
between different descriptions, a bridging edge is added so BFS can traverse it.
"""

from typed_composition_search import Registry


def build_graph(
    tools: list[dict],
    contracts: list[dict],
    compatibility: list[dict],
) -> Registry:
    """Build a Registry from extracted contracts and compatibility judgments.

    Parameters
    ----------
    tools : list[dict]
        Raw tool definitions (must have "id" and "desc" keys).
    contracts : list[dict]
        Output of extract_contracts — each has "tool", "consumes", "produces".
    compatibility : list[dict]
        Output of infer_compatibility — each has "source_tool", "target_tool",
        "source_produces", "target_consumes", "compatible".
    """
    contract_by_tool = {c["tool"]: c for c in contracts}
    tool_desc = {t["id"]: t["desc"] for t in tools}

    reg = Registry()

    for c in contracts:
        tool_id = c["tool"]
        consumes = c.get("consumes", [])
        produces = c.get("produces", [])

        if not consumes or not produces:
            continue

        input_types = tuple(consumes)
        output_types = tuple(produces)

        reg.register(
            name=tool_id,
            input_types=input_types,
            output_types=output_types,
            description=tool_desc.get(tool_id, ""),
        )

    compatible_edges = [e for e in compatibility if e.get("compatible", False)]

    for edge in compatible_edges:
        src_produces = edge["source_produces"]
        tgt_consumes = edge["target_consumes"]

        if src_produces == tgt_consumes:
            continue

        bridge_name = f"_bridge:{src_produces}→{tgt_consumes}"
        reg.register(
            name=bridge_name,
            input_types=(src_produces,),
            output_types=(tgt_consumes,),
            description="",
        )

    return reg
