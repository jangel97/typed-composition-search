from toolgraph import Graph, Path, Tool


def make_tool(name: str, input_type: str, output_type: str) -> Tool:
    return Tool(name=name, input_types=(input_type,), output_types=(output_type,))


class TestFindPath:
    def test_single_edge(self):
        g = Graph()
        t = make_tool("get_product", "ProductName", "Product")
        g.add_tool(t)

        result = g.find_path("ProductName", "Product")

        assert result == Path(types=["ProductName", "Product"], tools=[t])

    def test_chain(self):
        g = Graph()
        t1 = make_tool("get_product", "ProductName", "Product")
        t2 = make_tool("search_artifacts", "Product", "ArtifactList")
        t3 = make_tool("get_build", "ArtifactList", "Build")
        for t in (t1, t2, t3):
            g.add_tool(t)

        result = g.find_path("ProductName", "Build")

        assert result == Path(
            types=["ProductName", "Product", "ArtifactList", "Build"],
            tools=[t1, t2, t3],
        )

    def test_no_path(self):
        g = Graph()
        g.add_tool(make_tool("get_product", "ProductName", "Product"))

        assert g.find_path("ProductName", "Build") is None

    def test_same_source_and_target(self):
        g = Graph()

        result = g.find_path("Product", "Product")

        assert result == Path(types=["Product"], tools=[])

    def test_bfs_picks_shortest(self):
        g = Graph()
        direct = make_tool("direct", "A", "C")
        step1 = make_tool("step1", "A", "B")
        step2 = make_tool("step2", "B", "C")
        for t in (step1, step2, direct):
            g.add_tool(t)

        result = g.find_path("A", "C")

        assert result == Path(types=["A", "C"], tools=[direct])

    def test_cycle_does_not_loop(self):
        g = Graph()
        g.add_tool(make_tool("a_to_b", "A", "B"))
        g.add_tool(make_tool("b_to_a", "B", "A"))
        g.add_tool(make_tool("b_to_c", "B", "C"))

        result = g.find_path("A", "C")

        assert result is not None
        assert result.types == ["A", "B", "C"]

    def test_disconnected_graph(self):
        g = Graph()
        g.add_tool(make_tool("a_to_b", "A", "B"))
        g.add_tool(make_tool("x_to_y", "X", "Y"))

        assert g.find_path("A", "Y") is None

    def test_path_types_and_tools_aligned(self):
        g = Graph()
        t1 = make_tool("t1", "A", "B")
        t2 = make_tool("t2", "B", "C")
        t3 = make_tool("t3", "C", "D")
        for t in (t1, t2, t3):
            g.add_tool(t)

        result = g.find_path("A", "D")

        assert result is not None
        assert len(result.tools) == len(result.types) - 1
        for i, tool in enumerate(result.tools):
            assert result.types[i] in tool.input_types
            assert result.types[i + 1] in tool.output_types

    def test_multi_output_tool(self):
        g = Graph()
        multi = Tool(name="inspect", input_types=("Deployment",), output_types=("PodList", "ReplicaSet"))
        g.add_tool(multi)

        result = g.find_path("Deployment", "ReplicaSet")

        assert result is not None
        assert result.tools == [multi]
        assert result.types == ["Deployment", "ReplicaSet"]


class TestFindCandidateTools:
    def test_single_edge(self):
        g = Graph()
        g.add_tool(make_tool("get_project", "Org", "Project"))

        assert g.find_candidate_tools("Org", "Project") == {"get_project"}

    def test_parallel_edges(self):
        g = Graph()
        g.add_tool(make_tool("list_projects", "Org", "Project"))
        g.add_tool(make_tool("create_project", "Org", "Project"))

        assert g.find_candidate_tools("Org", "Project") == {"list_projects", "create_project"}

    def test_no_path(self):
        g = Graph()
        g.add_tool(make_tool("a_to_b", "A", "B"))

        assert g.find_candidate_tools("A", "C") == set()

    def test_same_source_target(self):
        g = Graph()

        assert g.find_candidate_tools("A", "A") == set()

    def test_multihop_collects_all_tools(self):
        g = Graph()
        g.add_tool(make_tool("list_orgs", "Platform", "Org"))
        g.add_tool(make_tool("create_org", "Platform", "Org"))
        g.add_tool(make_tool("get_projects", "Org", "Project"))

        candidates = g.find_candidate_tools("Platform", "Project")

        assert candidates == {"list_orgs", "create_org", "get_projects"}

    def test_only_shortest_path_tools(self):
        g = Graph()
        g.add_tool(make_tool("direct", "A", "C"))
        g.add_tool(make_tool("step1", "A", "B"))
        g.add_tool(make_tool("step2", "B", "C"))

        assert g.find_candidate_tools("A", "C") == {"direct"}
