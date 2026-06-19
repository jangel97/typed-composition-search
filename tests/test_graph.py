from typed_composition_search import Tool
from typed_composition_search.graph import CapabilityGraph


def _build_chain() -> list[Tool]:
    return [
        Tool("get_latest_build", frozenset({"Product"}), frozenset({"Build"})),
        Tool("get_pipeline", frozenset({"Build"}), frozenset({"Pipeline"})),
        Tool("get_ticket", frozenset({"Pipeline"}), frozenset({"Ticket"})),
        Tool("get_approver", frozenset({"Ticket"}), frozenset({"User"})),
    ]


def test_forward_reachable_full_chain():
    g = CapabilityGraph(_build_chain())
    types, tools = g.forward_reachable({"Product"})
    assert {"Product", "Build", "Pipeline", "Ticket", "User"} == types
    assert len(tools) == 4


def test_forward_reachable_partial():
    g = CapabilityGraph(_build_chain())
    types, tools = g.forward_reachable({"Build"})
    assert "Product" not in types
    assert "User" in types
    assert len(tools) == 3


def test_forward_reachable_no_match():
    g = CapabilityGraph(_build_chain())
    types, tools = g.forward_reachable({"Unknown"})
    assert types == {"Unknown"}
    assert len(tools) == 0


def test_backward_reachable_full_chain():
    g = CapabilityGraph(_build_chain())
    types, tools = g.backward_reachable({"User"})
    assert {"Product", "Build", "Pipeline", "Ticket", "User"} == types
    assert len(tools) == 4


def test_backward_reachable_partial():
    g = CapabilityGraph(_build_chain())
    types, tools = g.backward_reachable({"Pipeline"})
    assert "User" not in types
    assert "Product" in types
    assert len(tools) == 2


def test_backward_reachable_no_match():
    g = CapabilityGraph(_build_chain())
    types, tools = g.backward_reachable({"Unknown"})
    assert types == {"Unknown"}
    assert len(tools) == 0


def test_disconnected_tool_excluded():
    tools = _build_chain() + [
        Tool("unrelated", frozenset({"Foo"}), frozenset({"Bar"})),
    ]
    g = CapabilityGraph(tools)
    _, forward_tools = g.forward_reachable({"Product"})
    _, backward_tools = g.backward_reachable({"User"})
    assert Tool("unrelated", frozenset({"Foo"}), frozenset({"Bar"})) not in forward_tools
    assert Tool("unrelated", frozenset({"Foo"}), frozenset({"Bar"})) not in backward_tools


def test_multi_input_tool_forward():
    tools = [
        Tool("get_a", frozenset({"Start"}), frozenset({"A"})),
        Tool("get_b", frozenset({"Start"}), frozenset({"B"})),
        Tool("combine", frozenset({"A", "B"}), frozenset({"Result"})),
    ]
    g = CapabilityGraph(tools)
    types, fired = g.forward_reachable({"Start"})
    assert "Result" in types
    assert len(fired) == 3
