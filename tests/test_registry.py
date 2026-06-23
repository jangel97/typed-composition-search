from typed_composition_search import Registry


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
