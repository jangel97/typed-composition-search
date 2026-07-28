import argparse
import webbrowser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from benchmarks.report_data import load_and_preprocess
from benchmarks.report_filters import register_filters

TEMPLATE_DIR = Path(__file__).parent / "templates"
DEFAULT_RESULTS_DIR = Path(__file__).parent / "results"
DEFAULT_OUTPUT = Path(__file__).parent / "report.html"


def generate_html(context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    register_filters(env)
    template = env.get_template("base.html.j2")
    return template.render(**context)


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark HTML report")
    parser.add_argument("results_dir", nargs="?", default=str(DEFAULT_RESULTS_DIR),
                        help="Directory containing result JSON files")
    parser.add_argument("--output", "-o", default=str(DEFAULT_OUTPUT),
                        help="Output HTML file path")
    parser.add_argument("--open", action="store_true",
                        help="Open report in browser after generating")
    args = parser.parse_args()

    context = load_and_preprocess(Path(args.results_dir))
    html = generate_html(context)

    output = Path(args.output)
    output.write_text(html)
    print(f"Report written to {output}")

    if args.open:
        webbrowser.open(f"file://{output.resolve()}")


if __name__ == "__main__":
    main()
