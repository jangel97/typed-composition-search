from typed_composition_search import Registry


def build_registry() -> Registry:
    reg = Registry()

    # --- Namespaces ---
    reg.register("list_namespaces", ("Cluster",), ("NamespaceList",))
    reg.register("get_namespace", ("NamespaceName",), ("Namespace",))
    reg.register("create_namespace", ("NamespaceSpec",), ("Namespace",))
    reg.register("delete_namespace", ("Namespace",), ("DeletionResult",))
    reg.register("patch_namespace", ("Namespace",), ("Namespace",))

    # --- Pods ---
    reg.register("list_pods", ("Namespace",), ("PodList",))
    reg.register("get_pod", ("PodName",), ("Pod",))
    reg.register("get_pod_logs", ("Pod",), ("PodLogs",))
    reg.register("get_pod_events", ("Pod",), ("PodEvents",))
    reg.register("get_pod_metrics", ("Pod",), ("PodMetrics",))
    reg.register("exec_pod", ("Pod",), ("ExecSession",))
    reg.register("delete_pod", ("Pod",), ("DeletionResult",))
    reg.register("patch_pod", ("Pod",), ("Pod",))

    # --- Deployments ---
    reg.register("list_deployments", ("Namespace",), ("DeploymentList",))
    reg.register("get_deployment", ("DeploymentName",), ("Deployment",))
    reg.register("create_deployment", ("DeploymentSpec",), ("Deployment",))
    reg.register("delete_deployment", ("Deployment",), ("DeletionResult",))
    reg.register("scale_deployment", ("Deployment",), ("Deployment",))
    reg.register("restart_deployment", ("Deployment",), ("Deployment",))
    reg.register("rollout_status", ("Deployment",), ("RolloutStatus",))
    reg.register("rollout_history", ("Deployment",), ("RolloutHistory",))
    reg.register("get_deployment_pods", ("Deployment",), ("PodList",))

    # --- StatefulSets ---
    reg.register("list_statefulsets", ("Namespace",), ("StatefulSetList",))
    reg.register("get_statefulset", ("StatefulSetName",), ("StatefulSet",))
    reg.register("create_statefulset", ("StatefulSetSpec",), ("StatefulSet",))
    reg.register("delete_statefulset", ("StatefulSet",), ("DeletionResult",))
    reg.register("scale_statefulset", ("StatefulSet",), ("StatefulSet",))
    reg.register("get_statefulset_pods", ("StatefulSet",), ("PodList",))

    # --- DaemonSets ---
    reg.register("list_daemonsets", ("Namespace",), ("DaemonSetList",))
    reg.register("get_daemonset", ("DaemonSetName",), ("DaemonSet",))
    reg.register("create_daemonset", ("DaemonSetSpec",), ("DaemonSet",))
    reg.register("delete_daemonset", ("DaemonSet",), ("DeletionResult",))

    # --- Services ---
    reg.register("list_services", ("Namespace",), ("ServiceList",))
    reg.register("get_service", ("ServiceName",), ("Service",))
    reg.register("create_service", ("ServiceSpec",), ("Service",))
    reg.register("delete_service", ("Service",), ("DeletionResult",))
    reg.register("patch_service", ("Service",), ("Service",))
    reg.register("get_endpoints", ("Service",), ("Endpoints",))
    reg.register("get_service_pods", ("Service",), ("PodList",))

    # --- Ingress ---
    reg.register("list_ingresses", ("Namespace",), ("IngressList",))
    reg.register("get_ingress", ("IngressName",), ("Ingress",))
    reg.register("create_ingress", ("IngressSpec",), ("Ingress",))
    reg.register("delete_ingress", ("Ingress",), ("DeletionResult",))

    # --- Nodes ---
    reg.register("list_nodes", ("Cluster",), ("NodeList",))
    reg.register("get_node", ("NodeName",), ("Node",))
    reg.register("cordon_node", ("Node",), ("Node",))
    reg.register("uncordon_node", ("Node",), ("Node",))
    reg.register("drain_node", ("Node",), ("DrainResult",))
    reg.register("get_node_metrics", ("Node",), ("NodeMetrics",))
    reg.register("get_pod_node", ("Pod",), ("Node",))

    # --- Persistent Volumes ---
    reg.register("list_pvs", ("Cluster",), ("PVList",))
    reg.register("get_pv", ("PVName",), ("PersistentVolume",))
    reg.register("create_pv", ("PVSpec",), ("PersistentVolume",))
    reg.register("delete_pv", ("PersistentVolume",), ("DeletionResult",))

    # --- Persistent Volume Claims ---
    reg.register("list_pvcs", ("Namespace",), ("PVCList",))
    reg.register("get_pvc", ("PVCName",), ("PersistentVolumeClaim",))
    reg.register("create_pvc", ("PVCSpec",), ("PersistentVolumeClaim",))
    reg.register("delete_pvc", ("PersistentVolumeClaim",), ("DeletionResult",))
    reg.register("resize_pvc", ("PersistentVolumeClaim",), ("PersistentVolumeClaim",))

    # --- Storage Classes ---
    reg.register("list_storageclasses", ("Cluster",), ("StorageClassList",))
    reg.register("get_storageclass", ("StorageClassName",), ("StorageClass",))
    reg.register("create_storageclass", ("StorageClassSpec",), ("StorageClass",))
    reg.register("delete_storageclass", ("StorageClass",), ("DeletionResult",))

    # --- ConfigMaps ---
    reg.register("list_configmaps", ("Namespace",), ("ConfigMapList",))
    reg.register("get_configmap", ("ConfigMapName",), ("ConfigMap",))
    reg.register("create_configmap", ("ConfigMapSpec",), ("ConfigMap",))
    reg.register("delete_configmap", ("ConfigMap",), ("DeletionResult",))
    reg.register("patch_configmap", ("ConfigMap",), ("ConfigMap",))

    # --- Secrets ---
    reg.register("list_secrets", ("Namespace",), ("SecretList",))
    reg.register("get_secret", ("SecretName",), ("Secret",))
    reg.register("create_secret", ("SecretSpec",), ("Secret",))
    reg.register("delete_secret", ("Secret",), ("DeletionResult",))
    reg.register("patch_secret", ("Secret",), ("Secret",))

    # --- Jobs ---
    reg.register("list_jobs", ("Namespace",), ("JobList",))
    reg.register("get_job", ("JobName",), ("Job",))
    reg.register("create_job", ("JobSpec",), ("Job",))
    reg.register("delete_job", ("Job",), ("DeletionResult",))
    reg.register("get_job_logs", ("Job",), ("JobLogs",))
    reg.register("get_job_pods", ("Job",), ("PodList",))

    # --- CronJobs ---
    reg.register("list_cronjobs", ("Namespace",), ("CronJobList",))
    reg.register("get_cronjob", ("CronJobName",), ("CronJob",))
    reg.register("create_cronjob", ("CronJobSpec",), ("CronJob",))
    reg.register("delete_cronjob", ("CronJob",), ("DeletionResult",))
    reg.register("suspend_cronjob", ("CronJob",), ("CronJob",))
    reg.register("resume_cronjob", ("CronJob",), ("CronJob",))
    reg.register("get_cronjob_jobs", ("CronJob",), ("JobList",))

    # --- Events ---
    reg.register("list_events", ("Namespace",), ("EventList",))
    reg.register("get_event", ("EventName",), ("Event",))

    # --- RBAC ---
    reg.register("list_roles", ("Namespace",), ("RoleList",))
    reg.register("get_role", ("RoleName",), ("Role",))
    reg.register("create_role", ("RoleSpec",), ("Role",))
    reg.register("list_rolebindings", ("Namespace",), ("RoleBindingList",))
    reg.register("get_rolebinding", ("RoleBindingName",), ("RoleBinding",))
    reg.register("list_clusterroles", ("Cluster",), ("ClusterRoleList",))
    reg.register("get_clusterrole", ("ClusterRoleName",), ("ClusterRole",))
    reg.register("list_clusterrolebindings", ("Cluster",), ("ClusterRoleBindingList",))
    reg.register("get_clusterrolebinding", ("ClusterRoleBindingName",), ("ClusterRoleBinding",))

    # --- Network Policies ---
    reg.register("list_networkpolicies", ("Namespace",), ("NetworkPolicyList",))
    reg.register("get_networkpolicy", ("NetworkPolicyName",), ("NetworkPolicy",))
    reg.register("create_networkpolicy", ("NetworkPolicySpec",), ("NetworkPolicy",))
    reg.register("delete_networkpolicy", ("NetworkPolicy",), ("DeletionResult",))

    # --- Resource Quotas ---
    reg.register("list_resourcequotas", ("Namespace",), ("ResourceQuotaList",))
    reg.register("get_resourcequota", ("ResourceQuotaName",), ("ResourceQuota",))
    reg.register("create_resourcequota", ("ResourceQuotaSpec",), ("ResourceQuota",))

    # --- Limit Ranges ---
    reg.register("list_limitranges", ("Namespace",), ("LimitRangeList",))
    reg.register("get_limitrange", ("LimitRangeName",), ("LimitRange",))
    reg.register("create_limitrange", ("LimitRangeSpec",), ("LimitRange",))

    # --- HPAs ---
    reg.register("list_hpas", ("Namespace",), ("HPAList",))
    reg.register("get_hpa", ("HPAName",), ("HPA",))
    reg.register("create_hpa", ("HPASpec",), ("HPA",))
    reg.register("delete_hpa", ("HPA",), ("DeletionResult",))
    reg.register("get_deployment_hpa", ("Deployment",), ("HPA",))

    # --- Custom Resources ---
    reg.register("list_crds", ("Cluster",), ("CRDList",))
    reg.register("get_crd", ("CRDName",), ("CRD",))
    reg.register("create_crd", ("CRDSpec",), ("CRD",))
    reg.register("delete_crd", ("CRD",), ("DeletionResult",))

    # --- OpenShift: Routes ---
    reg.register("list_routes", ("Namespace",), ("RouteList",))
    reg.register("get_route", ("RouteName",), ("Route",))
    reg.register("get_service_route", ("Service",), ("Route",))
    reg.register("get_route_service", ("Route",), ("Service",))

    # --- OpenShift: BuildConfigs ---
    reg.register("list_buildconfigs", ("Namespace",), ("BuildConfigList",))
    reg.register("get_buildconfig", ("BuildConfigName",), ("BuildConfig",))

    # --- OpenShift: ImageStreams ---
    reg.register("list_imagestreams", ("Namespace",), ("ImageStreamList",))
    reg.register("get_imagestream", ("ImageStreamName",), ("ImageStream",))

    # --- OpenShift: Templates ---
    reg.register("list_templates", ("Namespace",), ("TemplateList",))
    reg.register("get_template", ("TemplateName",), ("Template",))

    # --- OpenShift: Cluster Operators ---
    reg.register("list_clusteroperators", ("Cluster",), ("ClusterOperatorList",))
    reg.register("get_clusteroperator", ("ClusterOperatorName",), ("ClusterOperator",))

    # --- OpenShift: MachineConfigs ---
    reg.register("list_machineconfigs", ("Cluster",), ("MachineConfigList",))
    reg.register("get_machineconfig", ("MachineConfigName",), ("MachineConfig",))

    # --- OpenShift: MachineConfigPools ---
    reg.register("list_machineconfigpools", ("Cluster",), ("MachineConfigPoolList",))
    reg.register("get_machineconfigpool", ("MachineConfigPoolName",), ("MachineConfigPool",))

    # --- Cross-resource relationships ---
    reg.register("select_pod", ("PodList",), ("Pod",))
    reg.register("select_deployment", ("DeploymentList",), ("Deployment",))
    reg.register("select_service", ("ServiceList",), ("Service",))
    reg.register("select_job", ("JobList",), ("Job",))
    reg.register("select_node", ("NodeList",), ("Node",))

    return reg


ENTITY_TYPES = {
    "Cluster": "The Kubernetes/OpenShift cluster itself",
    "Namespace": "A Kubernetes namespace",
    "Pod": "A Kubernetes pod",
    "PodLogs": "Log output from a pod",
    "PodEvents": "Events associated with a pod",
    "PodMetrics": "CPU and memory usage metrics for a pod",
    "Deployment": "A Kubernetes deployment",
    "RolloutStatus": "Current rollout status of a deployment",
    "RolloutHistory": "Revision history of a deployment",
    "StatefulSet": "A Kubernetes statefulset",
    "DaemonSet": "A Kubernetes daemonset",
    "Service": "A Kubernetes service",
    "Endpoints": "Network endpoints backing a service",
    "Ingress": "A Kubernetes ingress resource",
    "Node": "A Kubernetes cluster node",
    "NodeMetrics": "CPU and memory usage metrics for a node",
    "PersistentVolume": "A persistent volume",
    "PersistentVolumeClaim": "A persistent volume claim",
    "StorageClass": "A storage class",
    "ConfigMap": "A Kubernetes configmap",
    "Secret": "A Kubernetes secret",
    "Job": "A Kubernetes job",
    "JobLogs": "Log output from a job",
    "CronJob": "A Kubernetes cronjob",
    "Event": "A Kubernetes event",
    "Role": "A namespace-scoped RBAC role",
    "RoleBinding": "A namespace-scoped role binding",
    "ClusterRole": "A cluster-scoped RBAC role",
    "ClusterRoleBinding": "A cluster-scoped role binding",
    "NetworkPolicy": "A Kubernetes network policy",
    "ResourceQuota": "A resource quota",
    "LimitRange": "A limit range",
    "HPA": "A horizontal pod autoscaler",
    "CRD": "A custom resource definition",
    "Route": "An OpenShift route (exposes a service externally)",
    "BuildConfig": "An OpenShift build configuration",
    "ImageStream": "An OpenShift image stream",
    "Template": "An OpenShift template",
    "ClusterOperator": "An OpenShift cluster operator",
    "MachineConfig": "An OpenShift machine config",
    "MachineConfigPool": "An OpenShift machine config pool",
}
