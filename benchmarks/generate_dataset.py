"""Generate training data for entity type prediction — domain-generic.

Works with any domain that has a graph_snapshot.json and queries.py.
The benchmark queries are held out as the test set.

Usage:
    SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.generate_dataset stripe_mcp qwen
    SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.generate_dataset stripe_mcp qwen --dry-run
"""

from __future__ import annotations

import argparse
import importlib
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

from benchmarks.llm import get_llm_config, llm_completion

BENCHMARKS_DIR = Path(__file__).resolve().parent

PARAPHRASE_PROMPT = """\
You are generating training data for an entity type classifier.

Given this tool information and its type mapping, generate {n} diverse natural language queries that a user might ask which would require this tool.

Tool: {tool_name}
Description: {description}
source_type: {source_type} — {source_desc}
target_type: {target_type} — {target_desc}

Generate queries in these styles ({per_style} each):
1. Formal/professional
2. Short/imperative (under 8 words)
3. Conversational/casual
4. Question form
5. Vague/incomplete (use everyday language, avoid API jargon)

Rules:
- Each query should be a realistic user request
- Vary specific resource names and details
- Do not repeat the same query structure
- Do not include source_type or target_type names literally in the query

Output ONLY a JSON array of strings. No explanation."""

HARD_NEGATIVE_PROMPT = """\
You are generating hard negative training data for an entity type classifier.

The classifier must distinguish between these type pairs that share the same source:

Target pair (correct): {source_type} → {target_type}
Confusing pairs (different targets from same source):
{confusing_pairs}

Generate {n} queries that clearly map to one of the CONFUSING pairs (not the target pair).
Each query should be superficially similar to queries about {source_type} → {target_type} but actually request a different target.

For each query, include which confusing pair it maps to.

Output as a JSON array of objects: [{{"query": "...", "source_type": "{source_type}", "target_type": "..."}}]
No explanation."""


def load_graph(domain: str) -> dict:
    path = BENCHMARKS_DIR / domain / "graph_snapshot.json"
    with open(path) as f:
        return json.load(f)


def load_test_queries(domain: str) -> set[str]:
    mod = importlib.import_module(f"benchmarks.{domain}.queries")
    return {q["query"].strip().lower() for q in mod.QUERIES}


def group_tools_by_pair(graph: dict) -> dict[tuple[str, str], list[dict]]:
    core_types = set(graph["entity_types"].keys())
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for tool in graph["tools"]:
        for inp in tool["input_types"]:
            for out in tool["output_types"]:
                if inp in core_types and out in core_types:
                    groups[(inp, out)].append(tool)
    return dict(groups)


def generate_paraphrases(
    config: dict,
    pair: tuple[str, str],
    tools: list[dict],
    entity_types: dict[str, str],
    n: int = 10,
) -> list[dict]:
    source, target = pair
    tool = tools[0]

    per_style = max(1, n // 5)
    prompt = PARAPHRASE_PROMPT.format(
        n=n,
        per_style=per_style,
        tool_name=tool["name"],
        description=tool.get("description", ""),
        source_type=source,
        source_desc=entity_types.get(source, ""),
        target_type=target,
        target_desc=entity_types.get(target, ""),
    )

    for attempt in range(3):
        try:
            resp = llm_completion(
                config,
                [{"role": "user", "content": prompt}],
                temperature=0.8,
            )
            text = resp.choices[0].message.content or ""
            start = text.find("[")
            end = text.rfind("]") + 1
            if start == -1 or end == 0:
                continue
            queries = json.loads(text[start:end])
            if not isinstance(queries, list):
                continue
            return [
                {
                    "query": q.strip(),
                    "source_type": source,
                    "target_type": target,
                    "style": "paraphrase",
                }
                for q in queries
                if isinstance(q, str) and q.strip()
            ]
        except (json.JSONDecodeError, Exception) as e:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"  Failed to paraphrase {source}→{target}: {e}", file=sys.stderr)
            return []
    return []


def generate_hard_negatives(
    config: dict,
    source: str,
    target: str,
    other_targets: list[str],
    entity_types: dict[str, str],
    n: int = 5,
) -> list[dict]:
    confusing = "\n".join(
        f"- {source} → {t}: {entity_types.get(t, '')}" for t in other_targets[:5]
    )
    prompt = HARD_NEGATIVE_PROMPT.format(
        source_type=source,
        target_type=target,
        confusing_pairs=confusing,
        n=n,
    )

    for attempt in range(3):
        try:
            resp = llm_completion(
                config,
                [{"role": "user", "content": prompt}],
                temperature=0.8,
            )
            text = resp.choices[0].message.content or ""
            start = text.find("[")
            end = text.rfind("]") + 1
            if start == -1 or end == 0:
                continue
            items = json.loads(text[start:end])
            results = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                q = item.get("query", "").strip()
                st = item.get("source_type", source)
                tt = item.get("target_type", "")
                if q and tt and tt in entity_types:
                    results.append({
                        "query": q,
                        "source_type": st,
                        "target_type": tt,
                        "style": "hard_negative",
                    })
            return results
        except (json.JSONDecodeError, Exception) as e:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"  Failed hard negatives for {source}: {e}", file=sys.stderr)
            return []
    return []


def run(domain: str, model_name: str, dry_run: bool = False,
        n_per_pair: int = 10, n_neg: int = 5):
    graph = load_graph(domain)
    entity_types = graph["entity_types"]
    pairs = group_tools_by_pair(graph)
    test_queries = load_test_queries(domain)

    print(f"Domain: {domain}")
    print(f"Graph: {len(graph['tools'])} tools, {len(entity_types)} entity types")
    print(f"Valid (source, target) pairs: {len(pairs)}")
    print(f"Test queries (held out): {len(test_queries)}")
    print(f"Paraphrases per pair: {n_per_pair}")

    source_targets: dict[str, list[str]] = defaultdict(list)
    for src, tgt in pairs:
        source_targets[src].append(tgt)
    multi_target_sources = {s: ts for s, ts in source_targets.items() if len(ts) >= 3}
    print(f"Sources with 3+ targets (hard negative candidates): {len(multi_target_sources)}")

    if dry_run:
        print("\n--- DRY RUN ---")
        estimated = len(pairs) * n_per_pair
        neg_pairs = sum(min(len(ts), 5) for ts in multi_target_sources.values())
        estimated_neg = neg_pairs * n_neg
        print(f"Estimated paraphrases: ~{estimated}")
        print(f"Estimated hard negatives: ~{estimated_neg}")
        print(f"Estimated total: ~{estimated + estimated_neg}")
        print(f"Estimated LLM calls: ~{len(pairs) + neg_pairs}")
        return

    config = get_llm_config(model_name)
    all_examples: list[dict] = []
    pair_list = sorted(pairs.keys())

    print(f"\nGenerating paraphrases for {len(pair_list)} pairs...")
    for i, pair in enumerate(pair_list):
        src, tgt = pair
        tools = pairs[pair]
        results = generate_paraphrases(config, pair, tools, entity_types, n=n_per_pair)
        all_examples.extend(results)
        if (i + 1) % 20 == 0 or i == len(pair_list) - 1:
            print(f"  [{i+1}/{len(pair_list)}] {len(all_examples)} examples so far")

    print(f"\nParaphrases generated: {len(all_examples)}")

    print(f"\nGenerating hard negatives for {len(multi_target_sources)} sources...")
    neg_count = 0
    for i, (source, targets) in enumerate(sorted(multi_target_sources.items())):
        for target in targets[:3]:
            other = [t for t in targets if t != target]
            if not other:
                continue
            results = generate_hard_negatives(
                config, source, target, other, entity_types, n=n_neg
            )
            all_examples.extend(results)
            neg_count += len(results)
        if (i + 1) % 10 == 0 or i == len(multi_target_sources) - 1:
            print(f"  [{i+1}/{len(multi_target_sources)}] {neg_count} hard negatives")

    print(f"Hard negatives generated: {neg_count}")

    seen = set()
    filtered = []
    test_overlap = 0
    for ex in all_examples:
        key = ex["query"].strip().lower()
        if key in seen:
            continue
        if key in test_queries:
            test_overlap += 1
            continue
        seen.add(key)
        filtered.append(ex)

    print(f"\nDeduplication: {len(all_examples)} → {len(filtered)}")
    if test_overlap:
        print(f"Removed {test_overlap} queries overlapping with test set")

    random.seed(42)
    random.shuffle(filtered)

    out_path = BENCHMARKS_DIR / domain / "training_data.jsonl"
    with open(out_path, "w") as f:
        for ex in filtered:
            f.write(json.dumps(ex) + "\n")

    print(f"\nWritten {len(filtered)} examples to {out_path}")

    sources = {ex["source_type"] for ex in filtered}
    targets = {ex["target_type"] for ex in filtered}
    all_types = sources | targets
    missing = set(entity_types.keys()) - all_types
    print(f"Source types covered: {len(sources)}")
    print(f"Target types covered: {len(targets)}")
    print(f"Total types covered: {len(all_types)} / {len(entity_types)}")
    if missing:
        print(f"Missing types: {sorted(missing)}")

    from collections import Counter
    styles = Counter(ex["style"] for ex in filtered)
    print(f"\nStyle distribution:")
    for style, count in styles.most_common():
        print(f"  {style}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Generate type prediction training data")
    parser.add_argument("domain", help="Domain name (e.g. stripe_mcp, k8s_mcp)")
    parser.add_argument("model", nargs="?", default="qwen", help="Model for paraphrasing")
    parser.add_argument("--dry-run", action="store_true", help="Show stats without generating")
    parser.add_argument("--n-per-pair", type=int, default=10, help="Paraphrases per type pair")
    parser.add_argument("--n-neg", type=int, default=5, help="Hard negatives per source-target")
    args = parser.parse_args()

    run(args.domain, args.model, dry_run=args.dry_run,
        n_per_pair=args.n_per_pair, n_neg=args.n_neg)


if __name__ == "__main__":
    main()
