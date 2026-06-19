from typed_composition_search import Registry


def build_devops_registry() -> Registry:
    r = Registry()

    # ── CI/CD ──────────────────────────────────────────────────────────
    r.add_tool("list_products", [], ["ProductList"])
    r.add_tool("get_product", ["ProductList"], ["Product"])
    r.add_tool("get_latest_build", ["Product"], ["Build"])
    r.add_tool("list_builds", ["Product"], ["BuildList"])
    r.add_tool("get_build_logs", ["Build"], ["BuildLog"])
    r.add_tool("get_pipeline", ["Build"], ["Pipeline"])
    r.add_tool("list_pipeline_stages", ["Pipeline"], ["StageList"])
    r.add_tool("get_stage", ["StageList"], ["Stage"])
    r.add_tool("trigger_build", ["Product"], ["BuildTriggered"])
    r.add_tool("get_build_artifacts", ["Build"], ["ArtifactList"])

    # ── Kubernetes ─────────────────────────────────────────────────────
    r.add_tool("list_namespaces", [], ["NamespaceList"])
    r.add_tool("get_namespace", ["NamespaceList"], ["Namespace"])
    r.add_tool("list_pods", ["Namespace"], ["PodList"])
    r.add_tool("get_pod", ["PodList"], ["Pod"])
    r.add_tool("get_pod_logs", ["Pod"], ["PodLog"])
    r.add_tool("list_deployments", ["Namespace"], ["DeploymentList"])
    r.add_tool("get_deployment", ["DeploymentList"], ["Deployment"])
    r.add_tool("scale_deployment", ["Deployment"], ["DeploymentScaled"])
    r.add_tool("list_services", ["Namespace"], ["ServiceList"])
    r.add_tool("get_service", ["ServiceList"], ["Service"])

    # ── Git ─────────────────────────────────────────────────────────────
    r.add_tool("list_repos", ["Product"], ["RepoList"])
    r.add_tool("get_repo", ["RepoList"], ["Repo"])
    r.add_tool("list_branches", ["Repo"], ["BranchList"])
    r.add_tool("get_branch", ["BranchList"], ["Branch"])
    r.add_tool("list_commits", ["Repo"], ["CommitList"])
    r.add_tool("get_commit", ["CommitList"], ["Commit"])
    r.add_tool("get_commit_diff", ["Commit"], ["Diff"])
    r.add_tool("list_pull_requests", ["Repo"], ["PRList"])
    r.add_tool("get_pull_request", ["PRList"], ["PR"])

    # ── Jira / Ticketing ────────────────────────────────────────────────
    r.add_tool("list_jira_projects", [], ["JiraProjectList"])
    r.add_tool("get_jira_project", ["JiraProjectList"], ["JiraProject"])
    r.add_tool("list_tickets", ["JiraProject"], ["TicketList"])
    r.add_tool("get_ticket", ["TicketList"], ["Ticket"])
    r.add_tool("get_ticket_assignee", ["Ticket"], ["User"])
    r.add_tool("get_ticket_comments", ["Ticket"], ["CommentList"])
    r.add_tool("create_ticket", ["AlertDetail"], ["TicketCreated"])
    r.add_tool("update_ticket_status", ["Ticket"], ["TicketStatusUpdated"])

    # ── Monitoring ──────────────────────────────────────────────────────
    r.add_tool("list_alerts", [], ["AlertList"])
    r.add_tool("get_alert", ["AlertList"], ["Alert"])
    r.add_tool("get_alert_detail", ["Alert"], ["AlertDetail"])
    r.add_tool("get_alert_source", ["Alert"], ["Namespace"])
    r.add_tool("get_metrics", ["Namespace"], ["MetricData"])
    r.add_tool("get_logs", ["Pod"], ["LogData"])
    r.add_tool("list_dashboards", [], ["DashboardList"])
    r.add_tool("get_dashboard", ["DashboardList"], ["Dashboard"])

    # ── Messaging ───────────────────────────────────────────────────────
    r.add_tool("list_slack_channels", [], ["ChannelList"])
    r.add_tool("get_slack_channel", ["ChannelList"], ["Channel"])
    r.add_tool("send_slack_message", ["Channel", "Summary"], ["SlackMessageSent"])
    r.add_tool("summarize", ["ArtifactList"], ["Summary"])
    r.add_tool("list_email_recipients", [], ["RecipientList"])
    r.add_tool("send_email", ["RecipientList", "Summary"], ["EmailSent"])
    r.add_tool("create_incident", ["AlertDetail"], ["IncidentCreated"])
    r.add_tool("resolve_incident", ["IncidentCreated"], ["IncidentResolved"])

    # ── Cross-domain links ──────────────────────────────────────────────
    r.add_tool("get_pipeline_ticket", ["Pipeline"], ["TicketList"])
    r.add_tool("get_build_commit", ["Build"], ["Commit"])
    r.add_tool("get_build_deployment", ["Build"], ["Deployment"])
    r.add_tool("get_pr_build", ["PR"], ["Build"])

    return r
