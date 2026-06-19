from dataclasses import dataclass, field


@dataclass
class Query:
    name: str
    description: str
    initial: set[str]
    goal: set[str]
    required_tools: set[str]
    expected_plan: list[str] = field(default_factory=list)


QUERIES = [
    Query(
        name="ticket_assignee",
        description="Who is assigned to the ticket for the latest build?",
        initial={"Product"},
        goal={"User"},
        required_tools={
            "get_latest_build",
            "get_pipeline",
            "get_pipeline_ticket",
            "get_ticket",
            "get_ticket_assignee",
        },
    ),
    Query(
        name="artifacts_to_slack",
        description="Send the build artifacts to Slack",
        initial={"Build"},
        goal={"SlackMessageSent"},
        required_tools={
            "get_build_artifacts",
            "summarize",
            "send_slack_message",
            "list_slack_channels",
            "get_slack_channel",
        },
    ),
    Query(
        name="alert_pods",
        description="What pods are affected by this alert?",
        initial={"Alert"},
        goal={"PodList"},
        required_tools={
            "get_alert_source",
            "list_pods",
        },
    ),
    Query(
        name="build_diff",
        description="Get the diff for the commit that triggered this build",
        initial={"Build"},
        goal={"Diff"},
        required_tools={
            "get_build_commit",
            "get_commit_diff",
        },
    ),
    Query(
        name="alert_to_ticket",
        description="Create a Jira ticket from this alert",
        initial={"Alert"},
        goal={"TicketCreated"},
        required_tools={
            "get_alert_detail",
            "create_ticket",
        },
    ),
    Query(
        name="scale_build_deployment",
        description="Scale the deployment for this build",
        initial={"Build"},
        goal={"DeploymentScaled"},
        required_tools={
            "get_build_deployment",
            "scale_deployment",
        },
    ),
    Query(
        name="product_prs",
        description="What PRs are open for this product's repo?",
        initial={"Product"},
        goal={"PRList"},
        required_tools={
            "list_repos",
            "get_repo",
            "list_pull_requests",
        },
    ),
]
