from typed_composition_search import Registry, Tool


def _approver_registry() -> Registry:
    r = Registry()
    r.add_tool("get_latest_build", ["Product"], ["Build"])
    r.add_tool("get_pipeline", ["Build"], ["Pipeline"])
    r.add_tool("get_ticket", ["Pipeline"], ["Ticket"])
    r.add_tool("get_approver", ["Ticket"], ["User"])
    return r


def _slack_registry() -> Registry:
    r = Registry()
    r.add_tool("get_latest_drop", ["Product"], ["Drop"])
    r.add_tool("list_artifacts", ["Drop"], ["ArtifactList"])
    r.add_tool("summarize", ["ArtifactList"], ["Summary"])
    r.add_tool("send_slack", ["Summary"], ["SlackMessageSent"])
    return r


class TestRelevantTools:
    def test_approver_chain(self):
        r = _approver_registry()
        tools = r.relevant_tools({"Product"}, {"User"})
        names = {t.name for t in tools}
        assert names == {"get_latest_build", "get_pipeline", "get_ticket", "get_approver"}

    def test_slack_chain(self):
        r = _slack_registry()
        tools = r.relevant_tools({"Product"}, {"SlackMessageSent"})
        names = {t.name for t in tools}
        assert names == {"get_latest_drop", "list_artifacts", "summarize", "send_slack"}

    def test_excludes_unrelated_tools(self):
        r = _approver_registry()
        r.add_tool("send_email", ["EmailDraft"], ["EmailSent"])
        tools = r.relevant_tools({"Product"}, {"User"})
        names = {t.name for t in tools}
        assert "send_email" not in names
        assert len(names) == 4

    def test_partial_chain(self):
        r = _approver_registry()
        tools = r.relevant_tools({"Build"}, {"Ticket"})
        names = {t.name for t in tools}
        assert names == {"get_pipeline", "get_ticket"}

    def test_goal_already_in_initial(self):
        r = _approver_registry()
        tools = r.relevant_tools({"User"}, {"User"})
        assert tools == set()

    def test_unreachable_goal(self):
        r = _approver_registry()
        tools = r.relevant_tools({"Product"}, {"NonExistent"})
        assert tools == set()

    def test_multi_input_tool(self):
        r = Registry()
        r.add_tool("get_a", ["Start"], ["A"])
        r.add_tool("get_b", ["Start"], ["B"])
        r.add_tool("combine", ["A", "B"], ["Result"])
        tools = r.relevant_tools({"Start"}, {"Result"})
        names = {t.name for t in tools}
        assert names == {"get_a", "get_b", "combine"}


class TestPlan:
    def test_approver_chain_order(self):
        r = _approver_registry()
        plan = r.plan({"Product"}, {"User"})
        assert plan is not None
        names = [t.name for t in plan]
        assert names == ["get_latest_build", "get_pipeline", "get_ticket", "get_approver"]

    def test_slack_chain_order(self):
        r = _slack_registry()
        plan = r.plan({"Product"}, {"SlackMessageSent"})
        assert plan is not None
        names = [t.name for t in plan]
        assert names == ["get_latest_drop", "list_artifacts", "summarize", "send_slack"]

    def test_goal_already_satisfied(self):
        r = _approver_registry()
        plan = r.plan({"User"}, {"User"})
        assert plan == []

    def test_unreachable_returns_none(self):
        r = _approver_registry()
        plan = r.plan({"Product"}, {"NonExistent"})
        assert plan is None

    def test_multi_input_plan(self):
        r = Registry()
        r.add_tool("get_a", ["Start"], ["A"])
        r.add_tool("get_b", ["Start"], ["B"])
        r.add_tool("combine", ["A", "B"], ["Result"])
        plan = r.plan({"Start"}, {"Result"})
        assert plan is not None
        names = [t.name for t in plan]
        assert "combine" in names
        assert names.index("get_a") < names.index("combine")
        assert names.index("get_b") < names.index("combine")


class TestDecorator:
    def test_decorator_registers_tool(self):
        r = Registry()

        @r.tool(inputs=["Build"], outputs=["Pipeline"])
        def get_pipeline(build_id: str):
            pass

        tools = r.graph().tools
        assert len(tools) == 1
        assert tools[0].name == "get_pipeline"

    def test_decorator_preserves_function(self):
        r = Registry()

        @r.tool(inputs=["Build"], outputs=["Pipeline"])
        def get_pipeline(build_id: str):
            return "result"

        assert get_pipeline("123") == "result"
