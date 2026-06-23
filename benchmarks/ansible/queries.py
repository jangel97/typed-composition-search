QUERIES = [
    # ──────────────────────────────────────────────
    # Clean, well-structured queries (read + write)
    # ──────────────────────────────────────────────
    {
        "id": "inventory_host_facts",
        "category": "clean",
        "query": "Show me the facts for hosts in the production inventory",
        "source_type": "Inventory",
        "target_type": "HostFacts",
        "expected_tools": ["get_inventory_hosts", "select_host", "get_host_facts"],
    },
    {
        "id": "role_defaults",
        "category": "clean",
        "query": "What are the default variables for the database role?",
        "source_type": "Role",
        "target_type": "RoleDefaults",
        "expected_tools": ["get_role_defaults"],
    },
    {
        "id": "playbook_run_log",
        "category": "clean",
        "query": "Get the log from the last run of the deploy playbook",
        "source_type": "Playbook",
        "target_type": "RunLog",
        "expected_tools": ["list_runs", "select_run", "get_run_log"],
    },
    {
        "id": "module_doc",
        "category": "clean",
        "query": "Show me the documentation for the yum module",
        "source_type": "Module",
        "target_type": "ModuleDoc",
        "expected_tools": ["get_module_doc"],
    },
    {
        "id": "group_hosts",
        "category": "clean",
        "query": "What hosts are in the webservers group?",
        "source_type": "Group",
        "target_type": "Host",
        "expected_tools": ["get_group_hosts", "select_host"],
    },
    {
        "id": "collection_roles",
        "category": "clean",
        "query": "List the roles in the infrastructure collection",
        "source_type": "Collection",
        "target_type": "Role",
        "expected_tools": ["get_collection_roles", "select_role"],
    },
    {
        "id": "role_tasks",
        "category": "clean",
        "query": "What tasks are defined in the security hardening role?",
        "source_type": "Role",
        "target_type": "Task",
        "expected_tools": ["get_role_tasks", "select_task"],
    },
    {
        "id": "job_events",
        "category": "clean",
        "query": "Show me the job events for the nightly backup job",
        "source_type": "Job",
        "target_type": "JobEvent",
        "expected_tools": ["get_job_events", "select_job_event"],
    },
    {
        "id": "add_host_write",
        "category": "clean",
        "query": "Add the new staging server to the production inventory",
        "source_type": "Inventory",
        "target_type": "Host",
        "expected_tools": ["add_host"],
    },
    {
        "id": "launch_job",
        "category": "clean",
        "query": "Launch the compliance check job template",
        "source_type": "JobTemplate",
        "target_type": "Job",
        "expected_tools": ["launch_job_template"],
    },

    # ──────────────────────────────────────────────
    # Ambiguous queries
    # ──────────────────────────────────────────────
    {
        "id": "ambiguous_config",
        "category": "ambiguous",
        "query": "Tell me about the webserver configuration",
        "source_type": "Role",
        "target_type": "RoleDefaults",
        "expected_tools": ["get_role_defaults"],
    },
    {
        "id": "ambiguous_playbook",
        "category": "ambiguous",
        "query": "What does the deploy playbook do?",
        "source_type": "Playbook",
        "target_type": "Task",
        "expected_tools": ["get_playbook_plays", "select_play", "get_play_tasks", "select_task"],
    },
    {
        "id": "ambiguous_setup",
        "category": "ambiguous",
        "query": "Show me the database setup",
        "source_type": "Role",
        "target_type": "Task",
        "expected_tools": ["get_role_tasks", "select_task"],
    },

    # ──────────────────────────────────────────────
    # Multi-hop queries (explicit and implicit targets)
    # ──────────────────────────────────────────────
    {
        "id": "multihop_role_modules",
        "category": "multihop",
        "query": "What modules are used by tasks in the webserver role?",
        "source_type": "Role",
        "target_type": "Module",
        "expected_tools": ["get_role_tasks", "select_task", "get_task_module"],
    },
    {
        "id": "multihop_inventory_facts",
        "category": "multihop",
        "query": "Show me the facts for hosts in the db group of the production inventory",
        "source_type": "Inventory",
        "target_type": "HostFacts",
        "expected_tools": ["get_inventory_groups", "select_group", "get_group_hosts", "select_host", "get_host_facts"],
    },
    {
        "id": "multihop_run_results",
        "category": "multihop",
        "query": "Get the task results from the last run of the deploy playbook",
        "source_type": "Playbook",
        "target_type": "TaskResult",
        "expected_tools": ["list_runs", "select_run", "get_run_tasks", "select_task_result"],
    },
    {
        "id": "multihop_playbook_handlers",
        "category": "multihop",
        "query": "What handlers are triggered by roles in the site playbook?",
        "source_type": "Playbook",
        "target_type": "Handler",
        "expected_tools": ["get_playbook_plays", "select_play", "get_play_roles", "select_role", "get_role_handlers", "select_handler"],
    },
    {
        "id": "multihop_implicit_logs",
        "category": "multihop",
        "query": "The nightly backup playbook ran last night, what happened?",
        "source_type": "Playbook",
        "target_type": "RunLog",
        "expected_tools": ["list_runs", "select_run", "get_run_log"],
    },
    {
        "id": "multihop_implicit_collection",
        "category": "multihop",
        "query": "Which collections provide the modules used in the network role?",
        "source_type": "Role",
        "target_type": "Collection",
        "expected_tools": [],
    },

    # ──────────────────────────────────────────────
    # Synonym-heavy queries
    # ──────────────────────────────────────────────
    {
        "id": "synonym_machines",
        "category": "synonym",
        "query": "What machines are managed by this inventory?",
        "source_type": "Inventory",
        "target_type": "Host",
        "expected_tools": ["get_inventory_hosts", "select_host"],
    },
    {
        "id": "synonym_recipe",
        "category": "synonym",
        "query": "Show me the recipe for deploying nginx",
        "source_type": "Playbook",
        "target_type": "PlaybookVars",
        "expected_tools": ["get_playbook_vars"],
    },
    {
        "id": "synonym_actions",
        "category": "synonym",
        "query": "What actions does the firewall role perform?",
        "source_type": "Role",
        "target_type": "Task",
        "expected_tools": ["get_role_tasks", "select_task"],
    },
    {
        "id": "synonym_packages",
        "category": "synonym",
        "query": "Which packages does this automation install?",
        "source_type": "Role",
        "target_type": "Module",
        "expected_tools": ["get_role_tasks", "select_task", "get_task_module"],
    },
    {
        "id": "synonym_runbook",
        "category": "synonym",
        "query": "Where is the runbook for the incident response procedure?",
        "source_type": "Playbook",
        "target_type": "Play",
        "expected_tools": ["get_playbook_plays", "select_play"],
    },

    # ──────────────────────────────────────────────
    # Noisy real-world language
    # ──────────────────────────────────────────────
    {
        "id": "noisy_deploy_failed",
        "category": "noisy",
        "query": "Hey, the deploy failed again last night. Can you pull the logs?",
        "source_type": "Playbook",
        "target_type": "RunLog",
        "expected_tools": ["list_runs", "select_run", "get_run_log"],
    },
    {
        "id": "noisy_webserver_facts",
        "category": "noisy",
        "query": "Something is wrong with the webservers, can you check what facts Ansible has for them?",
        "source_type": "Group",
        "target_type": "HostFacts",
        "expected_tools": ["get_group_hosts", "select_host", "get_host_facts"],
    },
    {
        "id": "noisy_audit_modules",
        "category": "noisy",
        "query": "We need to audit which modules we're using in production. Start with the common role.",
        "source_type": "Role",
        "target_type": "Module",
        "expected_tools": ["get_role_tasks", "select_task", "get_task_module"],
    },
    {
        "id": "noisy_host_vars",
        "category": "noisy",
        "query": "A host in staging isn't getting configured right, can you check its variables?",
        "source_type": "Host",
        "target_type": "HostVars",
        "expected_tools": ["get_host_vars"],
    },

    # ──────────────────────────────────────────────
    # Multiple valid paths
    # ──────────────────────────────────────────────
    {
        "id": "multipath_host_vars",
        "category": "multipath",
        "query": "What variables apply to the webserver hosts?",
        "source_type": "Host",
        "target_type": "HostVars",
        "expected_tools": ["get_host_vars"],
    },
    {
        "id": "multipath_deploy_tasks",
        "category": "multipath",
        "query": "Show me the tasks for the deploy workflow",
        "source_type": "Playbook",
        "target_type": "Task",
        "expected_tools": ["get_playbook_plays", "select_play", "get_play_tasks", "select_task"],
    },
]
