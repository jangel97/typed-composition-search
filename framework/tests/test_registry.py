from tcs import Registry


class TestRegistry:
    def test_register_and_resolve(self):
        reg = Registry()
        reg.register("get_product", ("ProductName",), ("Product",))
        reg.register("search_artifacts", ("Product",), ("ArtifactList",))

        result = reg.resolve("ProductName", "ArtifactList")

        assert result is not None
        assert [t.name for t in result.tools] == ["get_product", "search_artifacts"]
        assert result.types == ["ProductName", "Product", "ArtifactList"]

    def test_resolve_no_path(self):
        reg = Registry()
        reg.register("get_product", ("ProductName",), ("Product",))

        assert reg.resolve("ProductName", "Build") is None

    def test_register_returns_tool(self):
        reg = Registry()
        tool = reg.register("get_product", ("ProductName",), ("Product",), description="Looks up a product")

        assert tool.name == "get_product"
        assert tool.input_types == ("ProductName",)
        assert tool.output_types == ("Product",)
        assert tool.description == "Looks up a product"

    def test_full_pipeline(self):
        reg = Registry()
        reg.register("get_product", ("ProductName",), ("Product",))
        reg.register("search_artifacts", ("Product",), ("ArtifactList",))
        reg.register("get_build", ("ArtifactList",), ("Build",))
        reg.register("get_pipeline_run", ("Build",), ("PipelineRunURL",))

        result = reg.resolve("ProductName", "PipelineRunURL")

        assert result is not None
        assert [t.name for t in result.tools] == [
            "get_product",
            "search_artifacts",
            "get_build",
            "get_pipeline_run",
        ]
        assert result.types == [
            "ProductName",
            "Product",
            "ArtifactList",
            "Build",
            "PipelineRunURL",
        ]

    def test_types_returns_all_nodes(self):
        reg = Registry()
        reg.register("get_product", ("ProductName",), ("Product",))
        reg.register("list_variants", ("Product",), ("VariantList",))

        assert reg.types() == {"ProductName", "Product", "VariantList"}

    def test_tools_property(self):
        reg = Registry()
        reg.register("t1", ("A",), ("B",))
        reg.register("t2", ("B",), ("C",))

        tools = reg.tools
        assert len(tools) == 2
        assert tools[0].name == "t1"
        assert tools[1].name == "t2"

    def test_entity_types_empty_by_default(self):
        reg = Registry()
        assert reg.entity_types == {}

    def test_set_entity_types(self):
        reg = Registry()
        reg.set_entity_types({"Product": "A product in the catalog", "Order": "A customer order"})

        assert reg.entity_types == {"Product": "A product in the catalog", "Order": "A customer order"}

    def test_entity_types_returns_copy(self):
        reg = Registry()
        reg.set_entity_types({"A": "desc"})
        et = reg.entity_types
        et["B"] = "other"
        assert "B" not in reg.entity_types
