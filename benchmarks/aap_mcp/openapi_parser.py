"""Parse AAP MCP Server OpenAPI specs into typed tool edges.

Reads the 4 JSON specs (controller, eda, galaxy, gateway) and extracts
operations with inferred input/output entity types suitable for building
a typed composition graph.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedOperation:
    operation_id: str
    service: str
    method: str
    path: str
    description: str
    input_types: tuple[str, ...]
    output_types: tuple[str, ...]
    response_schema_ref: str | None = None
    request_schema_ref: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.service}.{self.operation_id}"


# ---------------------------------------------------------------------------
# Resource-to-entity mapping
# ---------------------------------------------------------------------------

# Controller uses underscores, EDA uses hyphens, gateway uses underscores,
# galaxy is mixed. This map covers all top-level resources across services.
RESOURCE_ENTITY_MAP: dict[str, str] = {
    # Controller
    "activity_stream": "ActivityStream",
    "ad_hoc_commands": "AdHocCommand",
    "ad_hoc_command_events": "AdHocCommandEvent",
    "analytics": "Analytics",
    "bulk": "Bulk",
    "config": "Config",
    "constructed_inventories": "ConstructedInventory",
    "credential_input_sources": "CredentialInputSource",
    "credential_types": "CredentialType",
    "credentials": "Credential",
    "dashboard": "Dashboard",
    "execution_environments": "ExecutionEnvironment",
    "groups": "Group",
    "host_metrics": "HostMetric",
    "host_metric_summary_monthly": "HostMetricSummaryMonthly",
    "hosts": "Host",
    "instance_groups": "InstanceGroup",
    "instances": "Instance",
    "inventories": "Inventory",
    "inventory_sources": "InventorySource",
    "job_templates": "JobTemplate",
    "jobs": "Job",
    "labels": "Label",
    "notification_templates": "NotificationTemplate",
    "notifications": "Notification",
    "organizations": "Organization",
    "projects": "Project",
    "resource_access_list": "ResourceAccessList",
    "resource_types": "ResourceType",
    "resources": "Resource",
    "role_definitions": "RoleDefinition",
    "roles": "Role",
    "schedules": "Schedule",
    "settings": "Setting",
    "system_job_templates": "SystemJobTemplate",
    "system_jobs": "SystemJob",
    "teams": "Team",
    "unified_job_templates": "UnifiedJobTemplate",
    "unified_jobs": "UnifiedJob",
    "users": "User",
    "workflow_approval_templates": "WorkflowApprovalTemplate",
    "workflow_approvals": "WorkflowApproval",
    "workflow_job_template_nodes": "WorkflowJobTemplateNode",
    "workflow_job_templates": "WorkflowJobTemplate",
    "workflow_jobs": "WorkflowJob",
    "workflow_job_nodes": "WorkflowJobNode",
    # EDA (hyphens normalized to underscores in lookup)
    "activations": "Activation",
    "activation_instances": "ActivationInstance",
    "audit_rules": "AuditRule",
    "credential_input_sources": "EdaCredentialInputSource",
    "credential_types": "EdaCredentialType",
    "decision_environments": "DecisionEnvironment",
    "eda_credentials": "EdaCredential",
    "event_streams": "EventStream",
    "rulebooks": "Rulebook",
    "rulebook_processes": "RulebookProcess",
    # Gateway
    "activitystream": "ActivityStream",
    "app_urls": "AppUrl",
    "applications": "Application",
    "authenticator_maps": "AuthenticatorMap",
    "authenticator_plugins": "AuthenticatorPlugin",
    "authenticator_users": "AuthenticatorUser",
    "authenticators": "Authenticator",
    "ca_certificates": "CACertificate",
    "http_ports": "HTTPPort",
    "service_clusters": "ServiceCluster",
    "service_keys": "ServiceKey",
    "service_nodes": "ServiceNode",
    "tokens": "Token",
    # Galaxy
    "collections": "Collection",
    "collection_versions": "CollectionVersion",
    "namespaces": "Namespace",
    "imports": "Import",
    "tasks": "GalaxyTask",
    "artifacts": "Artifact",
}

# Sub-resource segments that map to known child entities
SUB_RESOURCE_MAP: dict[str, str] = {
    "hosts": "Host",
    "groups": "Group",
    "children": "Group",
    "jobs": "Job",
    "launch": "Job",
    "relaunch": "Job",
    "cancel": "JobCancel",
    "stdout": "UnifiedJobStdout",
    "activity_stream": "ActivityStream",
    "credentials": "Credential",
    "schedules": "Schedule",
    "notifications": "Notification",
    "labels": "Label",
    "survey_spec": "SurveySpec",
    "object_roles": "Role",
    "access_list": "AccessList",
    "notification_templates_started": "NotificationTemplate",
    "notification_templates_success": "NotificationTemplate",
    "notification_templates_error": "NotificationTemplate",
    "events": "JobEvent",
    "job_events": "JobEvent",
    "job_host_summaries": "JobHostSummary",
    "extra_credentials": "Credential",
    "inventory_sources": "InventorySource",
    "input_sources": "CredentialInputSource",
    "copy": "Copy",
    "test": "CredentialTest",
    "playbooks": "ProjectPlaybooks",
    "scm_inventory_sources": "InventorySource",
    "project_updates": "ProjectUpdate",
    "update": "ProjectUpdate",
    "sync": "InventorySourceUpdate",
    "variable_data": "VariableData",
    "ansible_facts": "AnsibleFacts",
    "ad_hoc_commands": "AdHocCommand",
    "all_hosts": "Host",
    "potential_children": "Group",
    "instances": "Instance",
    "health_check": "InstanceHealthCheck",
    "install": "CollectionInstall",
    "workflow_nodes": "WorkflowJobNode",
    "workflow_job_template_nodes": "WorkflowJobTemplateNode",
    "create_schedule": "Schedule",
    "always_nodes": "WorkflowJobTemplateNode",
    "success_nodes": "WorkflowJobTemplateNode",
    "failure_nodes": "WorkflowJobTemplateNode",
    # EDA sub-resources
    "logs": "ActivationInstanceLog",
    "actions": "AuditAction",
    "disable": "Activation",
    "enable": "Activation",
    "restart": "Activation",
    # Gateway sub-resources
    "users": "User",
    "teams": "Team",
    "role_assignments": "RoleAssignment",
}

# API path prefixes to strip per service
SERVICE_PATH_PREFIX: dict[str, re.Pattern] = {
    "controller": re.compile(r"^/api(/v2)?"),
    "eda": re.compile(r"^/?"),
    "gateway": re.compile(r"^/api(/gateway(/v1)?)?"),
    "galaxy": re.compile(r"^/api(/galaxy)?"),
}

# Paths to skip (meta/debug/ui endpoints, not real tools)
SKIP_PATTERNS: list[re.Pattern] = [
    re.compile(r"/api/?$"),
    re.compile(r"/api/v2/?$"),
    re.compile(r"/api/gateway/?$"),
    re.compile(r"/api/gateway/v1/?$"),
    re.compile(r"/api/galaxy/?$"),
    re.compile(r"/debug/"),
    re.compile(r"/config/?$"),
    re.compile(r"/dashboard/?$"),
    re.compile(r"/feature_flags"),
    re.compile(r"/auth/"),
    re.compile(r"/_ui/"),
    re.compile(r"/openapi\.(json|yaml)"),
    re.compile(r"/ping/?$"),
    re.compile(r"/me/?$"),
    re.compile(r"/docs/?$"),
    re.compile(r"/role_metadata/?$"),
]


def load_spec(path: str | Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _get_description(details: dict) -> str:
    return (
        details.get("x-ai-description", "")
        or details.get("summary", "")
        or details.get("description", "")
    )


def _extract_schema_ref(response_or_body: dict) -> str | None:
    content = response_or_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})
    ref = schema.get("$ref")
    if ref:
        return ref.rsplit("/", 1)[-1]
    return None


def _should_skip(path: str) -> bool:
    return any(p.search(path) for p in SKIP_PATTERNS)


def _strip_prefix(path: str, service: str) -> str:
    pattern = SERVICE_PATH_PREFIX.get(service)
    if pattern:
        return pattern.sub("", path).strip("/")
    return path.strip("/")


def _parse_path_segments(clean_path: str) -> list[str]:
    """Split a cleaned path into meaningful segments, removing {id} placeholders."""
    segments = [s for s in clean_path.split("/") if s and not re.match(r"^\{.+\}$", s)]
    return segments


def _segment_to_entity(segment: str) -> str | None:
    normalized = segment.replace("-", "_")
    if normalized in RESOURCE_ENTITY_MAP:
        return RESOURCE_ENTITY_MAP[normalized]
    return None


CONTEXT_OVERRIDES: dict[tuple[str, str], str] = {
    ("Activation", "instances"): "ActivationInstance",
    ("ActivationInstance", "logs"): "ActivationInstanceLog",
    ("AuditRule", "actions"): "AuditAction",
    ("AuditRule", "events"): "AuditEvent",
}


def infer_entities(path: str, service: str) -> tuple[str | None, str | None]:
    """Infer (parent_entity, child_entity) from a path.

    Returns (parent, None) for top-level resources, (parent, child)
    for sub-resources like /inventories/{id}/hosts/.
    """
    clean = _strip_prefix(path, service)
    segments = _parse_path_segments(clean)

    if not segments:
        return None, None

    parent = _segment_to_entity(segments[0])

    if len(segments) >= 2:
        child_segment = segments[-1]
        normalized_child = child_segment.replace("-", "_")

        override = CONTEXT_OVERRIDES.get((parent, normalized_child)) if parent else None
        if override:
            return parent, override

        child = SUB_RESOURCE_MAP.get(normalized_child)
        if child is None:
            child = _segment_to_entity(child_segment)
        if child and parent:
            return parent, child

    return parent, None


def _classify_operation(operation_id: str, method: str) -> str:
    """Classify an operation into: list, retrieve, create, update, destroy, action."""
    oid = operation_id.lower()
    if method == "delete" or oid.endswith("_destroy"):
        return "destroy"
    if method == "get":
        if oid.endswith("_list"):
            return "list"
        if oid.endswith("_retrieve"):
            return "retrieve"
        return "retrieve"
    if method in ("put", "patch") or oid.endswith(("_update", "_partial_update")):
        return "update"
    if method == "post":
        if oid.endswith("_create"):
            return "create"
        return "create"
    return "action"


def assign_types(
    operation_id: str,
    method: str,
    parent_entity: str | None,
    child_entity: str | None,
    response_ref: str | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Assign input_types and output_types based on CRUD classification."""
    if parent_entity is None:
        parent_entity = "Platform"

    op_class = _classify_operation(operation_id, method)

    if child_entity:
        # Sub-resource operation
        if op_class == "list":
            return (parent_entity,), (child_entity,)
        if op_class == "retrieve":
            return (parent_entity,), (child_entity,)
        if op_class == "create":
            return (parent_entity,), (child_entity,)
        if op_class == "destroy":
            return (parent_entity,), ("DeletionResult",)
        if op_class == "update":
            return (parent_entity,), (child_entity,)
        return (parent_entity,), (child_entity,)

    # Top-level resource
    if op_class == "list":
        return ("Platform",), (parent_entity,)
    if op_class == "retrieve":
        return (f"{parent_entity}Name",), (parent_entity,)
    if op_class == "create":
        return (f"{parent_entity}Spec",), (parent_entity,)
    if op_class == "update":
        return (parent_entity,), (parent_entity,)
    if op_class == "destroy":
        return (parent_entity,), ("DeletionResult",)
    return (parent_entity,), (parent_entity,)


def extract_operations(spec: dict, service: str) -> list[ParsedOperation]:
    """Extract all operations from an OpenAPI spec."""
    operations: list[ParsedOperation] = []
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        if _should_skip(path):
            continue

        for method, details in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue

            operation_id = details.get("operationId", "")
            if not operation_id:
                continue

            description = _get_description(details)

            response_ref = None
            responses = details.get("responses", {})
            for code in ("200", "201", "202"):
                if code in responses:
                    response_ref = _extract_schema_ref(responses[code])
                    if response_ref:
                        break

            request_ref = None
            request_body = details.get("requestBody", {})
            if request_body:
                request_ref = _extract_schema_ref(request_body)

            parent_entity, child_entity = infer_entities(path, service)
            input_types, output_types = assign_types(
                operation_id, method, parent_entity, child_entity, response_ref
            )

            operations.append(ParsedOperation(
                operation_id=operation_id,
                service=service,
                method=method,
                path=path,
                description=description,
                input_types=input_types,
                output_types=output_types,
                response_schema_ref=response_ref,
                request_schema_ref=request_ref,
            ))

    return operations


SPEC_FILES: dict[str, str] = {
    "controller": "controller-schema.json",
    "eda": "eda-openapi.json",
    "galaxy": "galaxy-openapi.json",
    "gateway": "gateway-schema.json",
}


def parse_all_specs(
    data_dir: str | Path,
    services: list[str] | None = None,
) -> list[ParsedOperation]:
    """Parse all OpenAPI specs and return typed operations.

    Args:
        data_dir: Path to the directory containing the JSON spec files.
        services: Optional list of services to include (default: all).

    Returns:
        List of ParsedOperation objects with inferred input/output types.
    """
    data_dir = Path(data_dir)
    all_ops: list[ParsedOperation] = []

    for service, filename in SPEC_FILES.items():
        if services and service not in services:
            continue
        spec_path = data_dir / filename
        if not spec_path.exists():
            continue
        spec = load_spec(spec_path)
        ops = extract_operations(spec, service)
        all_ops.extend(ops)

    return all_ops


def collect_entity_types(operations: list[ParsedOperation]) -> dict[str, str]:
    """Collect all unique entity types referenced by operations.

    Returns a dict of entity_name -> description suitable for LLM prompting.
    """
    entities: set[str] = set()
    for op in operations:
        entities.update(op.input_types)
        entities.update(op.output_types)

    # Remove synthetic types that shouldn't be in the LLM menu
    skip = {"DeletionResult", "Platform"}

    type_descriptions: dict[str, str] = {}
    for e in sorted(entities):
        if e in skip:
            continue
        type_descriptions[e] = _describe_entity(e)

    return type_descriptions


def _describe_entity(name: str) -> str:
    """Generate a human-readable description for an entity type."""
    descriptions: dict[str, str] = {
        "JobTemplate": "A configured job template that defines how to launch a playbook",
        "Job": "An execution of a job template",
        "JobCancel": "A cancelled job execution",
        "JobEvent": "An event emitted during job execution",
        "JobHostSummary": "Per-host summary of a job execution",
        "UnifiedJobStdout": "Standard output (logs) from a job execution",
        "WorkflowJobTemplate": "A workflow template composing multiple job templates",
        "WorkflowJob": "An execution of a workflow job template",
        "WorkflowJobTemplateNode": "A node in a workflow job template graph",
        "WorkflowJobNode": "A node in a running workflow job",
        "WorkflowApproval": "An approval step in a workflow",
        "WorkflowApprovalTemplate": "A template for approval steps in workflows",
        "Inventory": "A collection of managed hosts",
        "InventorySource": "An external source for dynamic inventory",
        "InventorySourceUpdate": "An update/sync of an inventory source",
        "ConstructedInventory": "A dynamically constructed inventory from other inventories",
        "Host": "A managed host/node in an inventory",
        "Group": "A group of hosts in an inventory",
        "VariableData": "Variables assigned to a host, group, or inventory",
        "AnsibleFacts": "Gathered facts about a host (OS, network, hardware, etc.)",
        "Credential": "A stored credential (machine, cloud, SCM, etc.)",
        "CredentialType": "A type/schema definition for credentials",
        "CredentialInputSource": "An external credential input source",
        "CredentialTest": "Result of testing a credential",
        "Project": "A source code repository containing playbooks and roles",
        "ProjectPlaybooks": "Playbooks available in a project",
        "ProjectUpdate": "An SCM update/sync of a project",
        "Organization": "An organizational unit for access control and grouping",
        "Team": "A team of users within an organization",
        "User": "A platform user account",
        "Role": "An RBAC role defining permissions",
        "RoleDefinition": "A definition of available role permissions",
        "RoleAssignment": "An assignment of a role to a user or team",
        "Schedule": "A scheduled execution of a job or workflow template",
        "NotificationTemplate": "A notification channel configuration (email, Slack, etc.)",
        "Notification": "A notification sent by a notification template",
        "ExecutionEnvironment": "A container image for running automation",
        "Instance": "An automation controller instance/node in the cluster",
        "InstanceGroup": "A group of controller instances for capacity isolation",
        "InstanceHealthCheck": "Health check result for an instance",
        "Label": "A label/tag applied to resources for organization",
        "ActivityStream": "An audit log entry of platform activity",
        "SystemJobTemplate": "A system maintenance job template (cleanup, etc.)",
        "SystemJob": "An execution of a system job template",
        "UnifiedJobTemplate": "Any job template type (job, workflow, project update, etc.)",
        "UnifiedJob": "Any job type (job, workflow job, project update, etc.)",
        "AdHocCommand": "An ad-hoc command execution on hosts",
        "AdHocCommandEvent": "An event from an ad-hoc command execution",
        "SurveySpec": "A survey/form specification for job template parameters",
        "AccessList": "Users/teams with access to a resource",
        "Copy": "A copy operation on a resource",
        "Setting": "A platform configuration setting",
        "Resource": "A generic platform resource",
        "ResourceType": "A type of platform resource",
        "Analytics": "Platform analytics and usage data",
        "Bulk": "Bulk operations on multiple resources",
        # EDA
        "Activation": "An EDA rulebook activation (running event processor)",
        "ActivationInstance": "A running instance of an EDA activation",
        "ActivationInstanceLog": "Logs from an EDA activation instance",
        "AuditAction": "An action triggered by an EDA audit rule",
        "AuditEvent": "An event captured by an EDA audit rule",
        "AuditRule": "An EDA audit rule for tracking rule firings",
        "DecisionEnvironment": "A container image for running EDA rulebooks",
        "EdaCredential": "A credential used by EDA activations",
        "EdaCredentialType": "A credential type for EDA",
        "EdaCredentialInputSource": "An external credential source for EDA",
        "EventStream": "An EDA event stream for receiving events",
        "Rulebook": "An EDA rulebook defining event-driven rules",
        "RulebookProcess": "A running EDA rulebook process",
        # Gateway
        "Authenticator": "An authentication provider (LDAP, SAML, OIDC, etc.)",
        "AuthenticatorMap": "A mapping rule for an authenticator",
        "AuthenticatorPlugin": "An available authenticator plugin type",
        "AuthenticatorUser": "A user account from an authenticator",
        "Application": "An OAuth2 application registration",
        "AppUrl": "A registered application URL in the gateway",
        "CACertificate": "A CA certificate for TLS verification",
        "HTTPPort": "An HTTP port configuration on the gateway",
        "ServiceCluster": "A cluster of automation services",
        "ServiceNode": "A node in a service cluster",
        "ServiceKey": "A service key for inter-service authentication",
        "Token": "An API token for authentication",
        # Galaxy
        "Collection": "An Ansible content collection",
        "CollectionVersion": "A specific version of an Ansible collection",
        "CollectionInstall": "Installation of a collection",
        "Namespace": "A namespace for organizing collections",
        "Import": "A collection import task",
        "GalaxyTask": "A background task in Galaxy",
        "Artifact": "A collection artifact/package",
    }

    if name in descriptions:
        return descriptions[name]

    if name.endswith("List"):
        base = name[:-4]
        base_desc = descriptions.get(base, base)
        return f"A list of {base_desc.lower() if isinstance(base_desc, str) and not base_desc[0].isupper() else base.lower() + 's'}"

    if name.endswith("Name"):
        base = name[:-4]
        return f"The name/identifier of a {base.lower()}"

    if name.endswith("Spec"):
        base = name[:-4]
        return f"Specification for creating a {base.lower()}"

    return f"A {name} entity in the automation platform"


if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "aap-mcp-server" / "data")

    ops = parse_all_specs(data_dir)
    entity_types = collect_entity_types(ops)

    print(f"Total operations: {len(ops)}")
    print(f"Entity types: {len(entity_types)}")
    print()

    by_service = {}
    for op in ops:
        by_service.setdefault(op.service, []).append(op)
    for svc, svc_ops in sorted(by_service.items()):
        print(f"  {svc}: {len(svc_ops)} operations")

    print(f"\nEntity types ({len(entity_types)}):")
    for name, desc in sorted(entity_types.items()):
        print(f"  {name}: {desc}")

    print(f"\nSample operations:")
    for op in ops[:10]:
        print(f"  {op.full_name}: {op.input_types} -> {op.output_types}")
