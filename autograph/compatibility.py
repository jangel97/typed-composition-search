"""Stage 2: Infer compositional compatibility between tool outputs and inputs.

Instead of clustering descriptions into types, directly asks: "can the output
of tool A be consumed by tool B?" This builds graph edges from compatibility
judgments rather than type equality.
"""

import json
from pathlib import Path

from benchmarks.llm import llm_completion

CACHE_DIR = Path(__file__).parent / "cache"

SYSTEM_PROMPT = """You are determining compositional compatibility between tool outputs and inputs.

For each pair, decide: can the output of the first tool be directly used as input to the second tool?

Consider semantic compatibility, not just modality. For example:
- A "condensed summary" CAN be used as input to a tool that consumes "text in a source language" (a summary is valid text for translation).
- A "generated image" CANNOT be used as input to a tool that consumes "text in a source language".
- An "image with bounding boxes" CAN be used as input to a tool that consumes "an image" (it's still an image).

Be permissive for genuine compatibility but strict about modality mismatches.

Respond with a JSON array where each element has:
{"source": "tool_A", "target": "tool_B", "compatible": true/false, "reason": "short explanation"}"""


def _build_pairs(contracts: list[dict]) -> list[tuple[dict, dict]]:
    pairs = []
    for a in contracts:
        for b in contracts:
            if a["tool"] == b["tool"]:
                continue
            for prod in a.get("produces", []):
                for cons in b.get("consumes", []):
                    pairs.append((a, b, prod, cons))
    return pairs


def infer_compatibility(
    contracts: list[dict],
    llm_config: dict,
    domain: str = "default",
    use_cache: bool = True,
    batch_size: int = 30,
) -> list[dict]:
    cache_path = CACHE_DIR / f"compatibility_{domain}.json"

    if use_cache and cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    pairs = _build_pairs(contracts)
    all_results = []

    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i + batch_size]

        pair_descriptions = []
        for idx, (a, b, prod, cons) in enumerate(batch):
            pair_descriptions.append(
                f'{idx + 1}. Tool "{a["tool"]}" produces: "{prod}" → '
                f'Tool "{b["tool"]}" consumes: "{cons}"'
            )

        user_prompt = (
            f"Determine compatibility for these {len(batch)} pairs:\n\n"
            + "\n".join(pair_descriptions)
        )

        response = llm_completion(
            llm_config,
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=4096,
        )

        text = (response.choices[0].message.content or "").strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            print(f"  Warning: no JSON array in batch {i // batch_size}, skipping")
            continue

        batch_results = json.loads(text[start:end])

        for result in batch_results:
            src = result.get("source")
            tgt = result.get("target")
            compat = result.get("compatible", False)

            matching = [
                (a, b, prod, cons) for a, b, prod, cons in batch
                if a["tool"] == src and b["tool"] == tgt
            ]
            if matching:
                a, b, prod, cons = matching[0]
                all_results.append({
                    "source_tool": src,
                    "target_tool": tgt,
                    "source_produces": prod,
                    "target_consumes": cons,
                    "compatible": compat,
                    "reason": result.get("reason", ""),
                })

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(all_results, f, indent=2)

    return all_results
