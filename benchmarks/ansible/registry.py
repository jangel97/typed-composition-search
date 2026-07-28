from typed_composition_search import Registry


def build_registry() -> Registry:
    reg = Registry()

    # --- Organizations ---
    reg.register("list_organizations", ("Platform",), ("OrganizationList",))
    reg.register("get_organization", ("OrganizationName",), ("Organization",))

    # --- Projects ---
    reg.register("list_projects", ("Organization",), ("ProjectList",))
    reg.register("get_project", ("ProjectName",), ("Project",))
    reg.register("create_project", ("ProjectSpec",), ("Project",))
    reg.register("delete_project", ("Project",), ("DeletionResult",))
    reg.register("sync_project", ("Project",), ("Project",))

    # --- Inventories ---
    reg.register("list_inventories", ("Organization",), ("InventoryList",))
    reg.register("get_inventory", ("InventoryName",), ("Inventory",))
    reg.register("create_inventory", ("InventorySpec",), ("Inventory",))
    reg.register("delete_inventory", ("Inventory",), ("DeletionResult",))
    reg.register("get_inventory_hosts", ("Inventory",), ("HostList",))
    reg.register("get_inventory_groups", ("Inventory",), ("GroupList",))
    reg.register("import_inventory", ("InventorySource",), ("Inventory",))

    # --- Hosts ---
    reg.register("get_host", ("HostName",), ("Host",))
    reg.register("get_host_vars", ("Host",), ("HostVars",))
    reg.register("get_host_facts", ("Host",), ("HostFacts",))
    reg.register("add_host", ("Inventory",), ("Host",))
    reg.register("remove_host", ("Host",), ("DeletionResult",))
    reg.register("enable_host", ("Host",), ("Host",))
    reg.register("disable_host", ("Host",), ("Host",))

    # --- Groups ---
    reg.register("get_group", ("GroupName",), ("Group",))
    reg.register("get_group_hosts", ("Group",), ("HostList",))
    reg.register("get_group_vars", ("Group",), ("GroupVars",))
    reg.register("create_group", ("Inventory",), ("Group",))
    reg.register("delete_group", ("Group",), ("DeletionResult",))
    reg.register("add_host_to_group", ("Group",), ("Host",))

    # --- Playbooks ---
    reg.register("list_playbooks", ("Project",), ("PlaybookList",))
    reg.register("get_playbook", ("PlaybookName",), ("Playbook",))
    reg.register("get_playbook_plays", ("Playbook",), ("PlayList",))
    reg.register("get_playbook_vars", ("Playbook",), ("PlaybookVars",))
    reg.register("run_playbook", ("Playbook",), ("PlaybookRun",))
    reg.register("lint_playbook", ("Playbook",), ("LintResult",))
    reg.register("validate_playbook", ("Playbook",), ("ValidationResult",))

    # --- Plays ---
    reg.register("get_play_tasks", ("Play",), ("TaskList",))
    reg.register("get_play_handlers", ("Play",), ("HandlerList",))
    reg.register("get_play_roles", ("Play",), ("RoleList",))
    reg.register("get_play_tags", ("Play",), ("TagList",))

    # --- Tasks ---
    reg.register("get_task_module", ("Task",), ("Module",))
    reg.register("get_task_result", ("Task",), ("TaskResult",))
    reg.register("get_task_tags", ("Task",), ("TagList",))

    # --- Roles ---
    reg.register("list_roles", ("Project",), ("RoleList",))
    reg.register("get_role", ("RoleName",), ("Role",))
    reg.register("get_role_tasks", ("Role",), ("TaskList",))
    reg.register("get_role_defaults", ("Role",), ("RoleDefaults",))
    reg.register("get_role_handlers", ("Role",), ("HandlerList",))
    reg.register("get_role_templates", ("Role",), ("TemplateList",))
    reg.register("get_role_dependencies", ("Role",), ("RoleList",))
    reg.register("get_role_vars", ("Role",), ("RoleVars",))
    reg.register("install_role", ("RoleSpec",), ("Role",))

    # --- Modules ---
    reg.register("list_modules", ("Collection",), ("ModuleList",))
    reg.register("get_module", ("ModuleName",), ("Module",))
    reg.register("get_module_doc", ("Module",), ("ModuleDoc",))
    reg.register("get_module_examples", ("Module",), ("ModuleExamples",))
    reg.register("get_module_collection", ("Module",), ("Collection",))

    # --- Collections ---
    reg.register("list_collections", ("Namespace",), ("CollectionList",))
    reg.register("get_collection", ("CollectionName",), ("Collection",))
    reg.register("get_collection_modules", ("Collection",), ("ModuleList",))
    reg.register("get_collection_roles", ("Collection",), ("RoleList",))
    reg.register("get_collection_plugins", ("Collection",), ("PluginList",))
    reg.register("install_collection", ("CollectionSpec",), ("Collection",))

    # --- Plugins ---
    reg.register("list_plugins", ("PluginType",), ("PluginList",))
    reg.register("get_plugin", ("PluginName",), ("Plugin",))
    reg.register("get_plugin_doc", ("Plugin",), ("PluginDoc",))

    # --- Job Templates (AAP/Tower) ---
    reg.register("list_job_templates", ("Project",), ("JobTemplateList",))
    reg.register("get_job_template", ("JobTemplateName",), ("JobTemplate",))
    reg.register("create_job_template", ("JobTemplateSpec",), ("JobTemplate",))
    reg.register("delete_job_template", ("JobTemplate",), ("DeletionResult",))
    reg.register("launch_job_template", ("JobTemplate",), ("Job",))

    # --- Jobs ---
    reg.register("list_jobs", ("JobTemplate",), ("JobList",))
    reg.register("get_job", ("JobName",), ("Job",))
    reg.register("get_job_log", ("Job",), ("JobLog",))
    reg.register("get_job_events", ("Job",), ("JobEventList",))
    reg.register("cancel_job", ("Job",), ("Job",))
    reg.register("relaunch_job", ("Job",), ("Job",))

    # --- Playbook Runs ---
    reg.register("list_runs", ("Playbook",), ("RunList",))
    reg.register("get_run", ("RunName",), ("PlaybookRun",))
    reg.register("get_run_log", ("PlaybookRun",), ("RunLog",))
    reg.register("get_run_stats", ("PlaybookRun",), ("RunStats",))
    reg.register("get_run_tasks", ("PlaybookRun",), ("TaskResultList",))

    # --- Templates (Jinja2) ---
    reg.register("get_template", ("TemplateName",), ("Template",))
    reg.register("render_template", ("Template",), ("RenderedTemplate",))

    # --- Vault ---
    reg.register("list_vaults", ("Project",), ("VaultList",))
    reg.register("decrypt_vault", ("Vault",), ("VaultContents",))
    reg.register("encrypt_vault", ("VaultSpec",), ("Vault",))

    # --- Credentials (AAP/Tower) ---
    reg.register("list_credentials", ("Organization",), ("CredentialList",))
    reg.register("get_credential", ("CredentialName",), ("Credential",))
    reg.register("create_credential", ("CredentialSpec",), ("Credential",))

    # --- Schedules ---
    reg.register("list_schedules", ("JobTemplate",), ("ScheduleList",))
    reg.register("get_schedule", ("ScheduleName",), ("Schedule",))
    reg.register("create_schedule", ("ScheduleSpec",), ("Schedule",))
    reg.register("delete_schedule", ("Schedule",), ("DeletionResult",))

    # --- Notifications ---
    reg.register("list_notifications", ("Organization",), ("NotificationList",))
    reg.register("get_notification", ("NotificationName",), ("Notification",))

    # --- Cross-resource selectors ---
    reg.register("select_host", ("HostList",), ("Host",))
    reg.register("select_group", ("GroupList",), ("Group",))
    reg.register("select_playbook", ("PlaybookList",), ("Playbook",))
    reg.register("select_play", ("PlayList",), ("Play",))
    reg.register("select_role", ("RoleList",), ("Role",))
    reg.register("select_task", ("TaskList",), ("Task",))
    reg.register("select_module", ("ModuleList",), ("Module",))
    reg.register("select_collection", ("CollectionList",), ("Collection",))
    reg.register("select_run", ("RunList",), ("PlaybookRun",))
    reg.register("select_job", ("JobList",), ("Job",))
    reg.register("select_task_result", ("TaskResultList",), ("TaskResult",))
    reg.register("select_handler", ("HandlerList",), ("Handler",))
    reg.register("select_plugin", ("PluginList",), ("Plugin",))
    reg.register("select_template", ("TemplateList",), ("Template",))
    reg.register("select_job_event", ("JobEventList",), ("JobEvent",))

    return reg


ENTITY_TYPES = {
    # Infrastructure
    "Organization": "An Ansible Automation Platform organization",
    "Project": "An Ansible project (git repo containing playbooks/roles)",
    "Inventory": "An Ansible inventory of managed hosts",
    "Host": "A managed host/node in an inventory",
    "HostVars": "Variables assigned to a specific host",
    "HostFacts": "Gathered facts about a host (OS, network, hardware)",
    "Group": "A group of hosts in an inventory",
    "GroupVars": "Variables assigned to a host group",
    # Content
    "Playbook": "An Ansible playbook",
    "PlaybookVars": "Variables defined in a playbook",
    "Play": "A play within a playbook",
    "Task": "A task within a play or role",
    "TaskResult": "The result/output of a task execution",
    "Role": "An Ansible role (reusable automation unit)",
    "RoleDefaults": "Default variables for a role",
    "RoleVars": "Variables defined in a role",
    "Handler": "A handler triggered by task notifications",
    "Tag": "A tag applied to tasks or plays for selective execution",
    "Template": "A Jinja2 template file",
    "RenderedTemplate": "The rendered output of a Jinja2 template",
    # Modules & Plugins
    "Module": "An Ansible module (unit of automation)",
    "ModuleDoc": "Documentation for a module",
    "ModuleExamples": "Usage examples for a module",
    "Collection": "An Ansible collection (distribution unit for roles, modules, plugins)",
    "Plugin": "An Ansible plugin (callback, filter, lookup, etc.)",
    "PluginDoc": "Documentation for a plugin",
    # Execution
    "JobTemplate": "An AAP job template (configured playbook launch)",
    "Job": "A job execution in AAP",
    "JobLog": "Log output from a job execution",
    "JobEvent": "An event from a job execution",
    "PlaybookRun": "A playbook execution run",
    "RunLog": "Log output from a playbook run",
    "RunStats": "Statistics from a playbook run (ok, changed, failed, skipped)",
    # Security
    "Vault": "An Ansible vault encrypted file",
    "VaultContents": "Decrypted contents of a vault file",
    "Credential": "A stored credential in AAP",
    # Scheduling
    "Schedule": "A scheduled job execution in AAP",
    "Notification": "A notification configuration in AAP",
    # Validation
    "LintResult": "Results from ansible-lint",
    "ValidationResult": "Results from playbook syntax validation",
}
