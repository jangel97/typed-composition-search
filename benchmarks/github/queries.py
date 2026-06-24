QUERIES = [
    # ──────────────────────────────────────────────
    # Clean, well-structured queries
    # ──────────────────────────────────────────────
    {
        "id": "pr_diff",
        "category": "clean",
        "query": "Show me the diff for pull request #42 in the frontend repo",
        "source_type": "PR",
        "target_type": "PRDiff",
        "expected_tools": ["get_pr_diff"],
    },
    {
        "id": "issue_labels",
        "category": "clean",
        "query": "What labels are on issue #15?",
        "source_type": "Issue",
        "target_type": "Label",
        "expected_tools": ["get_issue_labels"],
    },
    {
        "id": "branch_protection",
        "category": "clean",
        "query": "What are the branch protection rules for the main branch?",
        "source_type": "Branch",
        "target_type": "BranchProtection",
        "expected_tools": ["get_branch_protection"],
    },
    {
        "id": "release_assets",
        "category": "clean",
        "query": "List the downloadable assets for the v2.0.0 release",
        "source_type": "Release",
        "target_type": "Asset",
        "expected_tools": ["get_release_assets"],
    },
    {
        "id": "commit_diff",
        "category": "clean",
        "query": "Show me what files were changed in commit abc123",
        "source_type": "Commit",
        "target_type": "CommitDiff",
        "expected_tools": ["get_commit_diff"],
    },
    {
        "id": "workflow_run_logs",
        "category": "clean",
        "query": "Get the logs from the latest CI workflow run",
        "source_type": "WorkflowRun",
        "target_type": "RunLogs",
        "expected_tools": ["get_run_logs"],
    },
    {
        "id": "deployment_status",
        "category": "clean",
        "query": "What is the status of the latest production deployment?",
        "source_type": "Deployment",
        "target_type": "DeploymentStatus",
        "expected_tools": ["get_deployment_statuses"],
    },
    {
        "id": "check_run_annotations",
        "category": "clean",
        "query": "Show me the annotations on the failing lint check run",
        "source_type": "CheckRun",
        "target_type": "Annotation",
        "expected_tools": ["get_check_run_annotations"],
    },
    {
        "id": "repo_readme",
        "category": "clean",
        "query": "Show me the README for the docs repo",
        "source_type": "Repo",
        "target_type": "FileContent",
        "expected_tools": ["get_readme"],
    },
    {
        "id": "commit_statuses",
        "category": "clean",
        "query": "What are the CI statuses on commit abc123?",
        "source_type": "Commit",
        "target_type": "Status",
        "expected_tools": ["get_commit_statuses"],
    },

    # ──────────────────────────────────────────────
    # Ambiguous queries
    # ──────────────────────────────────────────────
    {
        "id": "ambiguous_changes",
        "category": "ambiguous",
        "query": "Show me the recent changes to the project",
        "source_type": "Repo",
        "target_type": "Commit",
        "expected_tools": ["list_repo_commits"],
    },
    {
        "id": "ambiguous_status",
        "category": "ambiguous",
        "query": "Is the build passing?",
        "source_type": "PR",
        "target_type": "CheckRun",
        "expected_tools": ["get_pr_checks"],
    },
    {
        "id": "ambiguous_feedback",
        "category": "ambiguous",
        "query": "What feedback has the team given on this?",
        "source_type": "PR",
        "target_type": "Review",
        "expected_tools": ["get_pr_reviews", "select_review"],
    },

    # ──────────────────────────────────────────────
    # Multi-hop queries
    # ──────────────────────────────────────────────
    {
        "id": "multihop_pr_job_logs",
        "category": "multihop",
        "query": "Get the CI job logs for pull request #55",
        "source_type": "PR",
        "target_type": "JobLogs",
        "expected_tools": ["get_pr_checks", "select_check_run", "get_check_run_job", "get_job_logs"],
    },
    {
        "id": "multihop_workflow_job_logs",
        "category": "multihop",
        "query": "Get the job logs from the latest run of the CI workflow",
        "source_type": "Workflow",
        "target_type": "JobLogs",
        "expected_tools": ["get_workflow_runs", "select_workflow_run", "get_run_jobs", "select_job", "get_job_logs"],
    },
    {
        "id": "multihop_repo_check_suites",
        "category": "multihop",
        "query": "Show me the check suites for the latest commit in the backend repo",
        "source_type": "Repo",
        "target_type": "CheckSuite",
        "expected_tools": ["list_repo_commits", "select_commit", "list_check_suites", "select_check_suite"],
    },
    {
        "id": "multihop_milestone_issue_labels",
        "category": "multihop",
        "query": "What labels are on issues in the v3.0 milestone?",
        "source_type": "Milestone",
        "target_type": "Label",
        "expected_tools": ["get_milestone_issues", "select_issue", "get_issue_labels"],
    },
    {
        "id": "multihop_team_repo_release",
        "category": "multihop",
        "query": "Get the latest release from repos owned by the platform team",
        "source_type": "Team",
        "target_type": "Release",
        "expected_tools": ["get_team_repos", "select_repo", "get_latest_release"],
    },
    {
        "id": "multihop_org_repo_branches",
        "category": "multihop",
        "query": "Show me the branches for repos in the acme-corp organization",
        "source_type": "Org",
        "target_type": "Branch",
        "expected_tools": ["list_repos", "select_repo", "list_branches", "select_branch"],
    },

    # ──────────────────────────────────────────────
    # Synonyms and alternative wording
    # ──────────────────────────────────────────────
    {
        "id": "synonym_ci_output",
        "category": "synonym",
        "query": "Show me the CI output for the deploy workflow",
        "source_type": "Workflow",
        "target_type": "RunLogs",
        "expected_tools": ["get_workflow_runs", "select_workflow_run", "get_run_logs"],
    },
    {
        "id": "synonym_changeset",
        "category": "synonym",
        "query": "What files were touched in this changeset?",
        "source_type": "Commit",
        "target_type": "CommitDiff",
        "expected_tools": ["get_commit_diff"],
    },
    {
        "id": "synonym_pipeline_results",
        "category": "synonym",
        "query": "Did the pipeline pass on the latest commit?",
        "source_type": "Commit",
        "target_type": "Status",
        "expected_tools": ["get_commit_statuses"],
    },
    {
        "id": "synonym_approval",
        "category": "synonym",
        "query": "Has anyone approved this merge request?",
        "source_type": "PR",
        "target_type": "Review",
        "expected_tools": ["get_pr_reviews", "select_review"],
    },
    {
        "id": "synonym_build_output",
        "category": "synonym",
        "query": "Show me the build log for the test job",
        "source_type": "Job",
        "target_type": "JobLogs",
        "expected_tools": ["get_job_logs"],
    },

    # ──────────────────────────────────────────────
    # Noisy real-world language
    # ──────────────────────────────────────────────
    {
        "id": "noisy_ci_broken",
        "category": "noisy",
        "query": "CI is red on my PR, can you check what went wrong? The PR number is 123",
        "source_type": "PR",
        "target_type": "CheckRun",
        "expected_tools": ["get_pr_checks"],
    },
    {
        "id": "noisy_release_files",
        "category": "noisy",
        "query": "I need to download the binaries from the latest release, where can I find them?",
        "source_type": "Repo",
        "target_type": "Asset",
        "expected_tools": ["get_latest_release", "get_release_assets"],
    },
    {
        "id": "noisy_who_reviewed",
        "category": "noisy",
        "query": "Did anyone review my pull request yet? It's been sitting there for a week, PR #77",
        "source_type": "PR",
        "target_type": "Review",
        "expected_tools": ["get_pr_reviews", "select_review"],
    },
    {
        "id": "noisy_deploy_status",
        "category": "noisy",
        "query": "Hey, we just deployed to production, can you check if it went through okay?",
        "source_type": "Repo",
        "target_type": "DeploymentStatus",
        "expected_tools": ["list_deployments", "select_deployment", "get_deployment_statuses"],
    },

    # ──────────────────────────────────────────────
    # Multi-path queries (multiple valid paths)
    # ──────────────────────────────────────────────
    {
        "id": "multipath_commit_checks",
        "category": "multipath",
        "query": "Are all checks passing on the latest commit?",
        "source_type": "Commit",
        "target_type": "Status",
        "expected_tools": ["get_commit_statuses"],
    },
    {
        "id": "multipath_pr_diff",
        "category": "multipath",
        "query": "What changed in the latest pull request on the backend repo?",
        "source_type": "Repo",
        "target_type": "PRDiff",
        "expected_tools": ["list_prs", "select_pr", "get_pr_diff"],
    },
]
