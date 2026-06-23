"""Diagnostic: inspect raw logprobs from greedy decoding (temperature=0)."""

import importlib
import math
from benchmarks.llm import get_llm_config, llm_completion
from benchmarks.run_benchmark_probs import Q1_PROMPT, build_type_list


def inspect_query(config, query_text, entity_types, type_names, expected_source):
    type_list = build_type_list(entity_types, type_names)
    system = Q1_PROMPT.format(type_list=type_list)

    response = llm_completion(
        config,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": query_text},
        ],
        temperature=0,
        max_tokens=20,
        logprobs=True,
        top_logprobs=5,
    )

    choice = response.choices[0]
    text = choice.message.content.strip()

    print(f"\n{'─'*70}")
    print(f"Query:    {query_text}")
    print(f"Expected: {expected_source}")
    print(f"Got:      {text}")
    print()

    if choice.logprobs and choice.logprobs.content:
        for i, tok in enumerate(choice.logprobs.content):
            prob = math.exp(tok.logprob)
            print(f"  Token {i}: {tok.token!r:>20}  logprob={tok.logprob:.4f}  prob={prob:.4f}")
            if tok.top_logprobs:
                for alt in tok.top_logprobs:
                    alt_prob = math.exp(alt.logprob)
                    print(f"    alt:   {alt.token!r:>20}  logprob={alt.logprob:.4f}  prob={alt_prob:.4f}")
    else:
        print("  (no logprobs returned)")


def main():
    config = get_llm_config("qwen")

    for domain in ["k8s", "ansible"]:
        reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
        queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
        entity_types = reg_mod.ENTITY_TYPES
        type_names = sorted(entity_types.keys())
        queries = queries_mod.QUERIES

        print(f"\n{'='*70}")
        print(f"  DOMAIN: {domain} ({len(type_names)} types)")
        print(f"{'='*70}")

        for q in queries[:4]:
            inspect_query(config, q["query"], entity_types, type_names, q["source_type"])


if __name__ == "__main__":
    main()
