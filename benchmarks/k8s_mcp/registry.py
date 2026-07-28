"""TCS registry for the official containers/kubernetes-mcp-server.

Tools extracted from the Go source at:
  https://github.com/containers/kubernetes-mcp-server

All 41 tools across 6 toolsets: core (pods, resources, events, namespaces,
nodes), helm, tekton, kubevirt, kiali.
"""

from typed_composition_search import Registry


def build_registry() -> Registry:
    reg = Registry()

    # ── Core: Pods (8 tools) ──
    reg.register("pods_list", ("Cluster",), ("PodList",),
                 "List all pods in the cluster from all namespaces")
    reg.register("pods_list_in_namespace", ("Namespace",), ("PodList",),
                 "List pods in a specific namespace")
    reg.register("pods_get", ("Namespace",), ("Pod",),
                 "Get a pod by name in a namespace")
    reg.register("pods_delete", ("Pod",), ("DeletionResult",),
                 "Delete a pod")
    reg.register("pods_top", ("Cluster",), ("PodMetrics",),
                 "List resource consumption for pods")
    reg.register("pods_exec", ("Pod",), ("ExecResult",),
                 "Execute a command in a pod")
    reg.register("pods_log", ("Pod",), ("PodLog",),
                 "Get logs from a pod")
    reg.register("pods_run", ("Namespace",), ("Pod",),
                 "Run a new pod from a container image")

    # ── Core: Resources (5 tools) ──
    reg.register("resources_list", ("Namespace",), ("ResourceList",),
                 "List Kubernetes resources by apiVersion and kind")
    reg.register("resources_get", ("Namespace",), ("Resource",),
                 "Get a Kubernetes resource by apiVersion, kind, and name")
    reg.register("resources_create_or_update", ("ResourceManifest",), ("Resource",),
                 "Create or update a Kubernetes resource via Server-Side Apply")
    reg.register("resources_delete", ("Resource",), ("DeletionResult",),
                 "Delete a Kubernetes resource")
    reg.register("resources_scale", ("Resource",), ("Scale",),
                 "Get or update the scale of a Kubernetes resource")

    # ── Core: Events (1 tool) ──
    reg.register("events_list", ("Namespace",), ("EventList",),
                 "List Kubernetes events for debugging and troubleshooting")

    # ── Core: Namespaces (1 tool) ──
    reg.register("namespaces_list", ("Cluster",), ("NamespaceList",),
                 "List all namespaces in the cluster")

    # ── Core: Nodes (3 tools) ──
    reg.register("nodes_log", ("Node",), ("NodeLog",),
                 "Get logs from a Kubernetes node")
    reg.register("nodes_stats_summary", ("Node",), ("NodeStats",),
                 "Get detailed resource usage statistics from a node")
    reg.register("nodes_top", ("Cluster",), ("NodeMetrics",),
                 "List resource consumption for nodes")

    # ── Helm (3 tools) ──
    reg.register("helm_install", ("Namespace",), ("HelmRelease",),
                 "Install a Helm chart to create a release")
    reg.register("helm_list", ("Namespace",), ("HelmReleaseList",),
                 "List Helm releases")
    reg.register("helm_uninstall", ("HelmRelease",), ("DeletionResult",),
                 "Uninstall a Helm release")

    # ── Tekton (5 tools) ──
    reg.register("tekton_pipeline_start", ("TektonPipeline",), ("TektonPipelineRun",),
                 "Start a Tekton pipeline")
    reg.register("tekton_pipelinerun_restart", ("TektonPipelineRun",), ("TektonPipelineRun",),
                 "Restart a Tekton pipeline run")
    reg.register("tekton_task_start", ("TektonTask",), ("TektonTaskRun",),
                 "Start a Tekton task")
    reg.register("tekton_taskrun_restart", ("TektonTaskRun",), ("TektonTaskRun",),
                 "Restart a Tekton task run")
    reg.register("tekton_taskrun_logs", ("TektonTaskRun",), ("TektonTaskRunLog",),
                 "Get logs from a Tekton task run")
    reg.register("tekton_pipelinerun_taskruns", ("TektonPipelineRun",), ("TektonTaskRun",),
                 "Get task runs from a pipeline run")

    # ── KubeVirt (4 tools) ──
    reg.register("vm_lifecycle", ("VirtualMachine",), ("VirtualMachine",),
                 "Manage VM lifecycle (start, stop, restart, pause, unpause, migrate)")
    reg.register("vm_clone", ("VirtualMachine",), ("VirtualMachine",),
                 "Clone a virtual machine")
    reg.register("vm_create", ("Namespace",), ("VirtualMachine",),
                 "Create a new virtual machine")
    reg.register("vm_guest_info", ("VirtualMachine",), ("VMGuestInfo",),
                 "Get guest agent information from a virtual machine")

    # ── Kiali / Istio (10 tools) ──
    reg.register("kiali_get_mesh_traffic_graph", ("Namespace",), ("MeshTrafficGraph",),
                 "Get service mesh traffic graph")
    reg.register("kiali_get_mesh_status", ("Cluster",), ("MeshStatus",),
                 "Get overall mesh status")
    reg.register("kiali_manage_istio_config_read", ("Namespace",), ("IstioConfig",),
                 "Read Istio configuration for a namespace")
    reg.register("kiali_manage_istio_config", ("IstioConfig",), ("IstioConfig",),
                 "Create, update, or delete Istio configuration")
    reg.register("kiali_list_or_get_resources", ("Namespace",), ("KialiResource",),
                 "List or get Kiali-managed resources")
    reg.register("kiali_list_traces", ("Namespace",), ("TraceList",),
                 "List distributed traces")
    reg.register("kiali_get_trace_details", ("Trace",), ("TraceDetails",),
                 "Get details of a specific trace")
    reg.register("kiali_get_pod_performance", ("Pod",), ("PodPerformance",),
                 "Get pod performance metrics from Kiali")
    reg.register("kiali_get_logs", ("Pod",), ("KialiPodLog",),
                 "Get pod logs via Kiali")
    reg.register("kiali_get_metrics", ("Namespace",), ("Metrics",),
                 "Get metrics for a namespace")

    # ── Selectors (bridge list → item) ──
    reg.register("select_pod", ("PodList",), ("Pod",),
                 "Select a specific pod from a pod list")
    reg.register("select_namespace", ("NamespaceList",), ("Namespace",),
                 "Select a specific namespace from a namespace list")
    reg.register("select_node", ("NodeMetrics",), ("Node",),
                 "Select a specific node")

    return reg


ENTITY_TYPES = {
    "Cluster": "The Kubernetes cluster (root entry point)",
    "Namespace": "A Kubernetes namespace",
    "Pod": "A running Kubernetes pod",
    "PodList": "A list of pods",
    "PodLog": "Log output from a pod container",
    "PodMetrics": "CPU and memory usage metrics for pods",
    "PodPerformance": "Pod performance metrics from service mesh",
    "ExecResult": "Output from executing a command in a pod",
    "Node": "A Kubernetes cluster node",
    "NodeLog": "Log output from a node (kubelet, kube-proxy)",
    "NodeStats": "Detailed resource usage statistics from a node",
    "NodeMetrics": "CPU and memory usage metrics for nodes",
    "Resource": "A generic Kubernetes resource",
    "ResourceList": "A list of Kubernetes resources",
    "ResourceManifest": "A YAML/JSON resource manifest for apply",
    "Scale": "Replica count of a scalable resource",
    "EventList": "Kubernetes events for troubleshooting",
    "NamespaceList": "A list of namespaces",
    "DeletionResult": "Result of deleting a resource",
    "HelmRelease": "A deployed Helm release",
    "HelmReleaseList": "A list of Helm releases",
    "TektonPipeline": "A Tekton pipeline definition",
    "TektonPipelineRun": "A running or completed Tekton pipeline",
    "TektonTask": "A Tekton task definition",
    "TektonTaskRun": "A running or completed Tekton task",
    "TektonTaskRunLog": "Logs from a Tekton task run",
    "VirtualMachine": "A KubeVirt virtual machine",
    "VMGuestInfo": "Guest agent information from a virtual machine",
    "MeshTrafficGraph": "Service mesh traffic topology graph",
    "MeshStatus": "Overall service mesh health status",
    "IstioConfig": "Istio service mesh configuration",
    "KialiResource": "A Kiali-managed service mesh resource",
    "TraceList": "A list of distributed traces",
    "Trace": "A specific distributed trace",
    "TraceDetails": "Detailed span information for a trace",
    "KialiPodLog": "Pod logs retrieved via Kiali",
    "Metrics": "Namespace-level metrics from service mesh",
}
