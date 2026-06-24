from typed_composition_search import Registry


def build_registry() -> Registry:
    reg = Registry()

    # --- Organizations ---
    reg.register("list_orgs", ("User",), ("OrgList",))
    reg.register("get_org", ("OrgName",), ("Org",))
    reg.register("get_org_members", ("Org",), ("MemberList",))

    # --- Repositories ---
    reg.register("list_repos", ("Org",), ("RepoList",))
    reg.register("list_user_repos", ("User",), ("RepoList",))
    reg.register("get_repo", ("RepoName",), ("Repo",))
    reg.register("get_repo_languages", ("Repo",), ("LanguageList",))
    reg.register("get_repo_topics", ("Repo",), ("TopicList",))
    reg.register("get_repo_contributors", ("Repo",), ("ContributorList",))
    reg.register("get_repo_teams", ("Repo",), ("TeamList",))
    reg.register("fork_repo", ("Repo",), ("Repo",))
    reg.register("delete_repo", ("Repo",), ("DeletionResult",))

    # --- Branches ---
    reg.register("list_branches", ("Repo",), ("BranchList",))
    reg.register("get_branch", ("BranchName",), ("Branch",))
    reg.register("get_branch_protection", ("Branch",), ("BranchProtection",))
    reg.register("delete_branch", ("Branch",), ("DeletionResult",))

    # --- Commits ---
    reg.register("list_commits", ("Branch",), ("CommitList",))
    reg.register("list_repo_commits", ("Repo",), ("CommitList",))
    reg.register("get_commit", ("CommitSHA",), ("Commit",))
    reg.register("get_commit_diff", ("Commit",), ("CommitDiff",))
    reg.register("get_commit_statuses", ("Commit",), ("StatusList",))
    reg.register("compare_commits", ("CommitRange",), ("CommitComparison",))

    # --- Pull Requests ---
    reg.register("list_prs", ("Repo",), ("PRList",))
    reg.register("get_pr", ("PRNumber",), ("PR",))
    reg.register("create_pr", ("PRSpec",), ("PR",))
    reg.register("merge_pr", ("PR",), ("MergeResult",))
    reg.register("close_pr", ("PR",), ("PR",))
    reg.register("get_pr_diff", ("PR",), ("PRDiff",))
    reg.register("get_pr_commits", ("PR",), ("CommitList",))
    reg.register("get_pr_files", ("PR",), ("FileList",))
    reg.register("get_pr_reviews", ("PR",), ("ReviewList",))
    reg.register("get_pr_comments", ("PR",), ("CommentList",))
    reg.register("get_pr_checks", ("PR",), ("CheckRunList",))
    reg.register("request_review", ("PR",), ("ReviewRequest",))

    # --- Issues ---
    reg.register("list_issues", ("Repo",), ("IssueList",))
    reg.register("get_issue", ("IssueNumber",), ("Issue",))
    reg.register("create_issue", ("IssueSpec",), ("Issue",))
    reg.register("close_issue", ("Issue",), ("Issue",))
    reg.register("get_issue_comments", ("Issue",), ("CommentList",))
    reg.register("get_issue_labels", ("Issue",), ("LabelList",))
    reg.register("get_issue_timeline", ("Issue",), ("TimelineEventList",))
    reg.register("add_issue_label", ("Issue",), ("Label",))

    # --- Labels ---
    reg.register("list_labels", ("Repo",), ("LabelList",))
    reg.register("get_label", ("LabelName",), ("Label",))
    reg.register("create_label", ("LabelSpec",), ("Label",))
    reg.register("delete_label", ("Label",), ("DeletionResult",))

    # --- Milestones ---
    reg.register("list_milestones", ("Repo",), ("MilestoneList",))
    reg.register("get_milestone", ("MilestoneName",), ("Milestone",))
    reg.register("get_milestone_issues", ("Milestone",), ("IssueList",))
    reg.register("create_milestone", ("MilestoneSpec",), ("Milestone",))

    # --- Reviews ---
    reg.register("get_review", ("ReviewID",), ("Review",))
    reg.register("get_review_comments", ("Review",), ("CommentList",))

    # --- Actions / Workflows ---
    reg.register("list_workflows", ("Repo",), ("WorkflowList",))
    reg.register("get_workflow", ("WorkflowName",), ("Workflow",))
    reg.register("get_workflow_runs", ("Workflow",), ("WorkflowRunList",))
    reg.register("trigger_workflow", ("Workflow",), ("WorkflowRun",))
    reg.register("get_workflow_run", ("WorkflowRunID",), ("WorkflowRun",))
    reg.register("get_run_logs", ("WorkflowRun",), ("RunLogs",))
    reg.register("get_run_jobs", ("WorkflowRun",), ("JobList",))
    reg.register("cancel_run", ("WorkflowRun",), ("WorkflowRun",))
    reg.register("rerun_workflow", ("WorkflowRun",), ("WorkflowRun",))

    # --- Actions / Jobs ---
    reg.register("get_job", ("JobID",), ("Job",))
    reg.register("get_job_logs", ("Job",), ("JobLogs",))
    reg.register("get_job_steps", ("Job",), ("StepList",))

    # --- Check Runs / Suites ---
    reg.register("get_check_run", ("CheckRunID",), ("CheckRun",))
    reg.register("get_check_run_annotations", ("CheckRun",), ("AnnotationList",))
    reg.register("get_check_run_job", ("CheckRun",), ("Job",))
    reg.register("list_check_suites", ("Commit",), ("CheckSuiteList",))
    reg.register("get_check_suite", ("CheckSuiteID",), ("CheckSuite",))
    reg.register("get_check_suite_runs", ("CheckSuite",), ("CheckRunList",))

    # --- Releases ---
    reg.register("list_releases", ("Repo",), ("ReleaseList",))
    reg.register("get_release", ("ReleaseName",), ("Release",))
    reg.register("get_latest_release", ("Repo",), ("Release",))
    reg.register("create_release", ("ReleaseSpec",), ("Release",))
    reg.register("get_release_assets", ("Release",), ("AssetList",))
    reg.register("delete_release", ("Release",), ("DeletionResult",))

    # --- Tags ---
    reg.register("list_tags", ("Repo",), ("TagList",))
    reg.register("get_tag", ("TagName",), ("Tag",))

    # --- Files / Content ---
    reg.register("get_file", ("FilePath",), ("FileContent",))
    reg.register("list_directory", ("DirectoryPath",), ("FileList",))
    reg.register("get_readme", ("Repo",), ("FileContent",))

    # --- Teams ---
    reg.register("list_teams", ("Org",), ("TeamList",))
    reg.register("get_team", ("TeamName",), ("Team",))
    reg.register("get_team_members", ("Team",), ("MemberList",))
    reg.register("get_team_repos", ("Team",), ("RepoList",))

    # --- Users ---
    reg.register("get_user", ("Username",), ("User",))
    reg.register("get_user_events", ("User",), ("EventList",))

    # --- Deployments ---
    reg.register("list_deployments", ("Repo",), ("DeploymentList",))
    reg.register("get_deployment", ("DeploymentID",), ("Deployment",))
    reg.register("get_deployment_statuses", ("Deployment",), ("DeploymentStatusList",))
    reg.register("create_deployment", ("DeploymentSpec",), ("Deployment",))

    # --- Environments ---
    reg.register("list_environments", ("Repo",), ("EnvironmentList",))
    reg.register("get_environment", ("EnvironmentName",), ("Environment",))
    reg.register("get_environment_secrets", ("Environment",), ("SecretList",))

    # --- Secrets ---
    reg.register("list_repo_secrets", ("Repo",), ("SecretList",))
    reg.register("get_secret", ("SecretName",), ("Secret",))

    # --- Webhooks ---
    reg.register("list_webhooks", ("Repo",), ("WebhookList",))
    reg.register("get_webhook", ("WebhookID",), ("Webhook",))
    reg.register("get_webhook_deliveries", ("Webhook",), ("DeliveryList",))

    # --- Packages ---
    reg.register("list_packages", ("Repo",), ("PackageList",))
    reg.register("get_package", ("PackageName",), ("Package",))
    reg.register("get_package_versions", ("Package",), ("PackageVersionList",))

    # --- Cross-resource selectors ---
    reg.register("select_repo", ("RepoList",), ("Repo",))
    reg.register("select_pr", ("PRList",), ("PR",))
    reg.register("select_issue", ("IssueList",), ("Issue",))
    reg.register("select_commit", ("CommitList",), ("Commit",))
    reg.register("select_branch", ("BranchList",), ("Branch",))
    reg.register("select_workflow", ("WorkflowList",), ("Workflow",))
    reg.register("select_workflow_run", ("WorkflowRunList",), ("WorkflowRun",))
    reg.register("select_job", ("JobList",), ("Job",))
    reg.register("select_release", ("ReleaseList",), ("Release",))
    reg.register("select_check_run", ("CheckRunList",), ("CheckRun",))
    reg.register("select_team", ("TeamList",), ("Team",))
    reg.register("select_deployment", ("DeploymentList",), ("Deployment",))
    reg.register("select_milestone", ("MilestoneList",), ("Milestone",))
    reg.register("select_review", ("ReviewList",), ("Review",))
    reg.register("select_label", ("LabelList",), ("Label",))
    reg.register("select_member", ("MemberList",), ("Member",))
    reg.register("select_check_suite", ("CheckSuiteList",), ("CheckSuite",))
    reg.register("select_asset", ("AssetList",), ("Asset",))
    reg.register("select_status", ("StatusList",), ("Status",))
    reg.register("select_annotation", ("AnnotationList",), ("Annotation",))
    reg.register("select_deployment_status", ("DeploymentStatusList",), ("DeploymentStatus",))
    reg.register("select_contributor", ("ContributorList",), ("Contributor",))
    reg.register("select_tag", ("TagList",), ("Tag",))
    reg.register("select_delivery", ("DeliveryList",), ("Delivery",))
    reg.register("select_package_version", ("PackageVersionList",), ("PackageVersion",))
    reg.register("select_step", ("StepList",), ("Step",))
    reg.register("select_environment", ("EnvironmentList",), ("Environment",))
    reg.register("select_secret", ("SecretList",), ("Secret",))
    reg.register("select_webhook", ("WebhookList",), ("Webhook",))
    reg.register("select_event", ("EventList",), ("Event",))
    reg.register("select_comment", ("CommentList",), ("Comment",))

    return reg


ENTITY_TYPES = {
    # Core
    "User": "A GitHub user account",
    "Org": "A GitHub organization",
    "Repo": "A GitHub repository",
    "Branch": "A git branch in a repository",
    "BranchProtection": "Branch protection rules",
    "Commit": "A git commit",
    "CommitDiff": "The diff of a commit (files changed)",
    "CommitComparison": "A comparison between two commits",
    # Pull Requests
    "PR": "A pull request",
    "PRDiff": "The diff of a pull request",
    "Review": "A review on a pull request",
    "ReviewRequest": "A review request on a pull request",
    # Issues
    "Issue": "A GitHub issue",
    "Label": "A label applied to issues or PRs",
    "Milestone": "A milestone grouping issues",
    # Comments
    "Comment": "A comment on an issue or review",
    # Actions / CI
    "Workflow": "A GitHub Actions workflow definition",
    "WorkflowRun": "An execution of a GitHub Actions workflow",
    "RunLogs": "Log output from a workflow run",
    "Job": "A job within a workflow run",
    "JobLogs": "Log output from a job",
    "Step": "A step within a job",
    # Check Runs
    "CheckRun": "A check run (CI status check)",
    "CheckSuite": "A check suite grouping check runs for a commit",
    "Annotation": "An annotation on a check run (warning/error)",
    "Status": "A commit status (CI result)",
    # Releases
    "Release": "A GitHub release",
    "Asset": "A release asset (downloadable file)",
    "Tag": "A git tag",
    # Files
    "FileContent": "Contents of a file in the repository",
    # Teams
    "Team": "A team within an organization",
    "Member": "A member of an org or team",
    "Contributor": "A contributor to a repository",
    # Deployments
    "Deployment": "A GitHub deployment",
    "DeploymentStatus": "Status of a deployment",
    "Environment": "A deployment environment",
    # Infrastructure
    "Secret": "A repository or environment secret",
    "Webhook": "A webhook configuration",
    "Delivery": "A webhook delivery event",
    "Package": "A GitHub package",
    "PackageVersion": "A version of a GitHub package",
    "Event": "A GitHub event (push, PR, etc.)",
    "Language": "A programming language used in a repo",
    "Topic": "A topic tag on a repository",
}
