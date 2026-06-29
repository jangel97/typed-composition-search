import math


def tool_set_metrics(resolved: set[str], expected: set[str]) -> tuple[float, float, float]:
    if not resolved and not expected:
        return 1.0, 1.0, 1.0
    if not resolved or not expected:
        return 0.0, 0.0, 0.0
    tp = len(resolved & expected)
    precision = tp / len(resolved) if resolved else 0.0
    recall = tp / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_vals):
        return sorted_vals[f]
    return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])


def avg(xs: list) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def std(xs: list) -> float:
    if len(xs) < 2:
        return 0.0
    m = avg(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def build_type_list(entity_types: dict, type_names: list[str]) -> str:
    lines = []
    for name in type_names:
        desc = entity_types.get(name, "")
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def match_type_name(text: str, type_names: list[str]) -> str | None:
    text = text.strip()
    type_map = {name.lower(): name for name in type_names}
    if text.lower() in type_map:
        return type_map[text.lower()]
    first_line = text.split("\n")[0].strip().rstrip(".")
    if first_line.lower() in type_map:
        return type_map[first_line.lower()]
    text_lower = text.lower()
    for name_lower in sorted(type_map, key=len, reverse=True):
        if text_lower.startswith(name_lower):
            return type_map[name_lower]
    return None


def format_metric(value: float, width: int = 5, fmt: str = ".2f") -> str:
    if value < 0:
        return " " * (width - 1) + "—"
    return f"{value:>{width}{fmt}}"


def format_pruning(n_tools: int, total_tools: int) -> str:
    if n_tools <= 0:
        return "     —"
    q_pruning = 1.0 - n_tools / total_tools
    return f"{q_pruning:>5.0%}"


def format_tools(n_tools: int) -> str:
    if n_tools <= 0:
        return "    —"
    return f"{n_tools:>5}"
