import argparse
import importlib.util
import json
import sys
import tempfile
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def load_registry(path: Path):
    spec = importlib.util.spec_from_file_location("registry", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_registry()


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize typed composition graphs")
    parser.add_argument("registries", nargs="+", help="Paths to registry.py files")
    args = parser.parse_args()

    graphs = {}
    for path_str in args.registries:
        path = Path(path_str).resolve()
        name = path.parent.name
        graph = load_registry(path)._graph
        graphs[name] = {**graph.to_json(), "metrics": graph.metrics()}

    template = (Path(__file__).parent / "index.html").read_text()
    injection = f"<script>window.allGraphs = {json.dumps(graphs)};</script>"
    html = template.replace("</head>", injection + "\n</head>")

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        tmp_path = f.name

    print(f"Opening {tmp_path}")
    webbrowser.open(f"file://{tmp_path}")


if __name__ == "__main__":
    main()
