QUERIES = [
    # ──────────────────────────────────────────────
    # Clean, well-structured queries
    # ──────────────────────────────────────────────
    {
        "id": "deployment_logs",
        "category": "clean",
        "query": "Get the logs for pods running the nginx deployment in the production namespace",
        "source_type": "Namespace",
        "target_type": "PodLogs",
        "expected_tools": ["list_pods", "select_pod", "get_pod_logs"],
    },
    {
        "id": "pod_events",
        "category": "clean",
        "query": "Show me the events for pods in the api-gateway deployment",
        "source_type": "Deployment",
        "target_type": "PodEvents",
        "expected_tools": ["get_deployment_pods", "select_pod", "get_pod_events"],
    },
    {
        "id": "node_metrics",
        "category": "clean",
        "query": "What is the resource usage of the node running my database pod?",
        "source_type": "Pod",
        "target_type": "NodeMetrics",
        "expected_tools": ["get_pod_node", "get_node_metrics"],
    },
    {
        "id": "deployment_hpa",
        "category": "clean",
        "query": "Is the HPA configured for the worker deployment?",
        "source_type": "Deployment",
        "target_type": "HPA",
        "expected_tools": ["get_deployment_hpa"],
    },
    {
        "id": "service_route",
        "category": "clean",
        "query": "What is the OpenShift route for the frontend service?",
        "source_type": "Service",
        "target_type": "Route",
        "expected_tools": ["get_service_route"],
    },
    {
        "id": "service_endpoints",
        "category": "clean",
        "query": "Show me the endpoints backing the payment service in the checkout namespace",
        "source_type": "Namespace",
        "target_type": "Endpoints",
        "expected_tools": ["list_services", "select_service", "get_endpoints"],
    },
    {
        "id": "cronjob_logs",
        "category": "clean",
        "query": "Get the logs from the latest job of the cleanup cronjob",
        "source_type": "CronJob",
        "target_type": "JobLogs",
        "expected_tools": ["get_cronjob_jobs", "select_job", "get_job_logs"],
    },
    {
        "id": "rollout_status",
        "category": "clean",
        "query": "What is the rollout status of the auth deployment?",
        "source_type": "Deployment",
        "target_type": "RolloutStatus",
        "expected_tools": ["rollout_status"],
    },
    {
        "id": "pod_metrics",
        "category": "clean",
        "query": "Show me the CPU and memory usage for pods in the monitoring namespace",
        "source_type": "Namespace",
        "target_type": "PodMetrics",
        "expected_tools": ["list_pods", "select_pod", "get_pod_metrics"],
    },
    {
        "id": "statefulset_pod_logs",
        "category": "clean",
        "query": "Get the logs from the postgres statefulset pods",
        "source_type": "StatefulSet",
        "target_type": "PodLogs",
        "expected_tools": ["get_statefulset_pods", "select_pod", "get_pod_logs"],
    },

    # ──────────────────────────────────────────────
    # Ambiguous queries
    # ──────────────────────────────────────────────
    {
        "id": "ambiguous_info",
        "category": "ambiguous",
        "query": "Show me information about the frontend application",
        "source_type": "Deployment",
        "target_type": "Deployment",
        "expected_tools": [],
    },
    {
        "id": "ambiguous_logs",
        "category": "ambiguous",
        "query": "Get logs for the payment service",
        "source_type": "Service",
        "target_type": "PodLogs",
        "expected_tools": [],
    },
    {
        "id": "ambiguous_status",
        "category": "ambiguous",
        "query": "Is the checkout service running?",
        "source_type": "Service",
        "target_type": "Endpoints",
        "expected_tools": ["get_endpoints"],
    },

    # ──────────────────────────────────────────────
    # Multi-hop queries
    # ──────────────────────────────────────────────
    {
        "id": "multihop_node",
        "category": "multihop",
        "query": "What node is running the latest pod created by the api deployment?",
        "source_type": "Deployment",
        "target_type": "Node",
        "expected_tools": ["get_deployment_pods", "select_pod", "get_pod_node"],
    },
    {
        "id": "multihop_deploy_node_metrics",
        "category": "multihop",
        "query": "Show me the resource usage of nodes running the cache deployment pods",
        "source_type": "Deployment",
        "target_type": "NodeMetrics",
        "expected_tools": ["get_deployment_pods", "select_pod", "get_pod_node", "get_node_metrics"],
    },
    {
        "id": "multihop_ns_node",
        "category": "multihop",
        "query": "Which nodes are the pods in the staging namespace running on?",
        "source_type": "Namespace",
        "target_type": "Node",
        "expected_tools": ["list_pods", "select_pod", "get_pod_node"],
    },
    {
        "id": "multihop_cronjob_events",
        "category": "multihop",
        "query": "Show me the pod events for the latest run of the nightly-backup cronjob",
        "source_type": "CronJob",
        "target_type": "PodEvents",
        "expected_tools": ["get_cronjob_jobs", "select_job", "get_job_pods", "select_pod", "get_pod_events"],
    },

    # ──────────────────────────────────────────────
    # Synonyms and alternative wording
    # ──────────────────────────────────────────────
    {
        "id": "synonym_workload",
        "category": "synonym",
        "query": "Show me the workload behind the frontend app",
        "source_type": "Deployment",
        "target_type": "Deployment",
        "expected_tools": [],
    },
    {
        "id": "synonym_microservice",
        "category": "synonym",
        "query": "Which microservice owns this route?",
        "source_type": "Route",
        "target_type": "Service",
        "expected_tools": [],
    },
    {
        "id": "synonym_containers",
        "category": "synonym",
        "query": "How many replicas does the auth workload have?",
        "source_type": "Deployment",
        "target_type": "HPA",
        "expected_tools": ["get_deployment_hpa"],
    },
    {
        "id": "synonym_scaling",
        "category": "synonym",
        "query": "Is auto-scaling enabled for the worker deployment?",
        "source_type": "Deployment",
        "target_type": "HPA",
        "expected_tools": ["get_deployment_hpa"],
    },

    # ──────────────────────────────────────────────
    # Noisy real-world language
    # ──────────────────────────────────────────────
    {
        "id": "noisy_broken",
        "category": "noisy",
        "query": "Hey, I think the payment service is broken. Can you show me the logs from whatever pods are backing it?",
        "source_type": "Service",
        "target_type": "PodLogs",
        "expected_tools": [],
    },
    {
        "id": "noisy_wrong",
        "category": "noisy",
        "query": "Something seems wrong with the API. Can you figure out where it is running?",
        "source_type": "Deployment",
        "target_type": "Node",
        "expected_tools": ["get_deployment_pods", "select_pod", "get_pod_node"],
    },
    {
        "id": "noisy_crashing",
        "category": "noisy",
        "query": "The checkout pods keep crashing, can you check the events and see what's going on?",
        "source_type": "Pod",
        "target_type": "PodEvents",
        "expected_tools": ["get_pod_events"],
    },
    {
        "id": "noisy_slow",
        "category": "noisy",
        "query": "Users are complaining the app is slow. Can you check if the nodes are overloaded?",
        "source_type": "Namespace",
        "target_type": "NodeMetrics",
        "expected_tools": ["list_pods", "select_pod", "get_pod_node", "get_node_metrics"],
    },
]
