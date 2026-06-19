from typed_composition_search import Tool


def test_creation():
    t = Tool(name="get_build", inputs=frozenset({"Product"}), outputs=frozenset({"Build"}))
    assert t.name == "get_build"
    assert t.inputs == frozenset({"Product"})
    assert t.outputs == frozenset({"Build"})


def test_frozen():
    t = Tool(name="get_build", inputs=frozenset({"Product"}), outputs=frozenset({"Build"}))
    assert hash(t) is not None


def test_equality():
    a = Tool(name="get_build", inputs=frozenset({"Product"}), outputs=frozenset({"Build"}))
    b = Tool(name="get_build", inputs=frozenset({"Product"}), outputs=frozenset({"Build"}))
    assert a == b


def test_usable_in_set():
    t = Tool(name="get_build", inputs=frozenset({"Product"}), outputs=frozenset({"Build"}))
    s = {t, t}
    assert len(s) == 1
