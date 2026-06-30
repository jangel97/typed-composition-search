"""Stage 1: Extract semantic contracts from tool descriptions.

For each tool, asks an LLM to describe what it specifically consumes
and produces — not in type-system terms, but as natural language
descriptions of the data that flows in and out.
"""

import json
from pathlib import Path

from benchmarks.llm import llm_completion

CACHE_DIR = Path(__file__).parent / "cache"

SYSTEM_PROMPT = """You are analyzing tools to extract their semantic contracts.

For each tool, describe:
- **consumes**: What specific kind of data does this tool take as input? Be precise — distinguish between different kinds of the same modality (e.g., "a document or article" vs "a text prompt" vs "translated text").
- **produces**: What specific kind of data does this tool output? Again, be precise about what exactly is produced.

Use short, specific phrases (3-8 words each). Do NOT use generic terms like "text" or "image" alone — always qualify what kind.

Respond with a JSON array where each element has:
{"tool": "...", "consumes": ["..."], "produces": ["..."]}"""


def extract_contracts(
    tools: list[dict],
    llm_config: dict,
    domain: str = "default",
    use_cache: bool = True,
) -> list[dict]:
    cache_path = CACHE_DIR / f"contracts_{domain}.json"

    if use_cache and cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    tool_descriptions = []
    for t in tools:
        tool_descriptions.append(f'- {t["id"]}: {t["desc"]}')

    user_prompt = "Extract semantic contracts for these tools:\n\n" + "\n".join(tool_descriptions)

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
        raise ValueError(f"No JSON array found in response: {text[:200]}")

    contracts = json.loads(text[start:end])

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(contracts, f, indent=2)

    return contracts


def load_taskbench_tools(domain: str = "huggingface") -> list[dict]:
    data_dir = Path(__file__).parent.parent / "benchmarks" / "taskbench" / "data"
    filename = "hf_tools.json" if domain == "huggingface" else "mm_tools.json"
    with open(data_dir / filename) as f:
        return json.load(f)["nodes"]
