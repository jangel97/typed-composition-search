# toolgraph

Tool routing via typed composition graphs. Register tools with input/output entity types, then resolve multi-step tool chains automatically using graph search.

Instead of asking an LLM to select from hundreds of tools, reduce the problem to entity type prediction — then let the graph find the shortest tool chain.

## Install

```bash
pip install toolgraph
```

For LLM-based type prediction:

```bash
pip install toolgraph[llm]
```

## Quick start

```python
from toolgraph import Registry

reg = Registry()

# Register tools with typed inputs/outputs
reg.register("get_deployment", ("DeploymentName",), ("Deployment",))
reg.register("get_pods", ("Deployment",), ("PodList",))
reg.register("select_pod", ("PodList",), ("Pod",))
reg.register("get_logs", ("Pod",), ("PodLogs",))

# Resolve a tool chain
path = reg.resolve("DeploymentName", "PodLogs")

print(path.types)  # ['DeploymentName', 'Deployment', 'PodList', 'Pod', 'PodLogs']
print(path.tools)  # [get_deployment, get_pods, select_pod, get_logs]
```

## Graph analysis

```python
# What types can be reached from a given type?
reg.reachable_types("Deployment")  # {'PodList', 'Pod', 'PodLogs'}

# What types can reach a given target?
reg.reverse_reachable_types("PodLogs")  # {'Pod', 'PodList', 'Deployment', 'DeploymentName'}

# All known entity types
reg.types()  # {'DeploymentName', 'Deployment', 'PodList', 'Pod', 'PodLogs'}

# Structural metrics (degree distribution, centrality, reachability)
reg.graph.metrics()
```

## LLM type prediction (optional)

Use `TypePredictor` to automatically predict source/target entity types from natural language queries, then resolve the tool chain.

```python
from toolgraph import Registry
from toolgraph.predict import TypePredictor

reg = Registry()
reg.register("get_deployment", ("DeploymentName",), ("Deployment",))
reg.register("get_pods", ("Deployment",), ("PodList",))
reg.register("select_pod", ("PodList",), ("Pod",))
reg.register("get_logs", ("Pod",), ("PodLogs",))

# Provide entity type descriptions for the LLM
predictor = TypePredictor(
    model="gpt-4o",  # any litellm-compatible model
    entity_types={
        "DeploymentName": "The name of a Kubernetes deployment",
        "Deployment": "A Kubernetes deployment object",
        "PodList": "A list of pods",
        "Pod": "A single running pod",
        "PodLogs": "Log output from a pod",
    },
)

# Predict types from a query
prediction = predictor.predict("show me logs from the nginx deployment")
print(prediction.source_type)  # 'DeploymentName'
print(prediction.target_type)  # 'PodLogs'

# End-to-end: predict + resolve in one call
path = predictor.resolve("show me logs from the nginx deployment", reg)
print([t.name for t in path.tools])  # ['get_deployment', 'get_pods', 'select_pod', 'get_logs']
```

## API reference

### `Tool(name, input_types, output_types, description="")`

A typed transformation. Frozen dataclass. Multiple `input_types` are treated as OR (the tool is reachable from any single input type), not AND. The graph models sequential composition; tools requiring multiple inputs simultaneously are not supported.

### `Registry`

| Method | Description |
|--------|-------------|
| `register(name, input_types, output_types, description="")` | Register a tool, returns `Tool` |
| `resolve(source_type, target_type)` | Find shortest tool chain, returns `Path` or `None` |
| `reachable_types(source_type)` | All types reachable via forward traversal |
| `reverse_reachable_types(target_type)` | All types that can reach target |
| `types()` | All entity types in the graph |
| `tools` | List of registered `Tool` objects |
| `graph` | Underlying `Graph` instance |
| `entity_types` | Dict of type name to description |
| `set_entity_types(dict)` | Set type descriptions (for LLM prediction) |

### `Path`

| Field | Description |
|-------|-------------|
| `types` | List of entity types in the chain |
| `tools` | List of tools connecting them (`len(tools) == len(types) - 1`) |

### `TypePredictor(model, entity_types, **litellm_kwargs)` (requires `[llm]`)

| Method | Description |
|--------|-------------|
| `predict(query)` | Returns `Prediction(source_type, target_type)` |
| `resolve(query, registry)` | Predict + resolve, returns `Path` or `None` |

## License

Apache 2.0
