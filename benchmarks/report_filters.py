from jinja2 import Environment


def fmt_val(val, fmt_str=".2f"):
    if val is None:
        return "&mdash;"
    return f"{val:{fmt_str}}"


def f1_to_color(val):
    if val is None or val < 0:
        return "transparent"
    hue = int(val * 120)
    return f"hsla({hue}, 70%, 40%, 0.3)"


def delta_cls(delta):
    if delta > 0.005:
        return "delta-pos"
    if delta < -0.005:
        return "delta-neg"
    return ""


def delta_sign(delta):
    return "+" if delta > 0.005 else ""


def metric_cls(val, threshold_good=0.8, threshold_bad=0.5):
    if val is None or val < 0:
        return "na"
    if val >= threshold_good:
        return "delta-pos"
    if val < threshold_bad:
        return "delta-neg"
    return ""


def register_filters(env: Environment):
    env.filters["fmt_val"] = fmt_val
    env.filters["f1_color"] = f1_to_color
    env.filters["delta_cls"] = delta_cls
    env.filters["delta_sign"] = delta_sign
    env.filters["metric_cls"] = metric_cls
