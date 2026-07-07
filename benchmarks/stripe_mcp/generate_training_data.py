"""Generate template-based training data for Stripe entity type prediction.

Deterministic — no LLM calls. Generates ~3,000-4,000 examples from the
graph snapshot using query templates across 7 styles.
"""

from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


# ── Entity name conversion ────────────────────────────────────────────


def _pascal_to_words(name: str) -> str:
    words = re.findall(r"[A-Z][a-z]*|[A-Z]+(?=[A-Z]|$)", name)
    return " ".join(w.lower() for w in words)


def _pluralize(name: str) -> str:
    if name.endswith("y") and not name.endswith("ey"):
        return name[:-1] + "ies"
    if name.endswith("s") or name.endswith("x") or name.endswith("sh"):
        return name + "es"
    return name + "s"


def entity_name(pascal: str) -> str:
    return _pascal_to_words(pascal)


def entity_plural(pascal: str) -> str:
    return _pluralize(_pascal_to_words(pascal))


# ── Templates ─────────────────────────────────────────────────────────

PLATFORM_LIST_TEMPLATES = [
    "List all {plural}",
    "Show all {plural}",
    "Get the {plural}",
    "What {plural} do we have?",
    "Pull up the {plural}",
    "Show me all {plural} on the platform",
    "Can you list the {plural}?",
    "I need to see the {plural}",
    "Display all {plural}",
    "Fetch all available {plural}",
]

SUBRESOURCE_TEMPLATES = [
    "Show the {child_plural} for this {parent}",
    "List {parent}'s {child_plural}",
    "Get {child_plural} on this {parent}",
    "What {child_plural} does this {parent} have?",
    "Show me the {child_plural} associated with this {parent}",
    "Retrieve the {child_plural} for a specific {parent}",
    "List all {child_plural} under this {parent}",
    "Get the {child_plural} linked to this {parent}",
]

RETRIEVE_TEMPLATES = [
    "Get {name} details",
    "Show this {name}",
    "Retrieve the {name} information",
    "Look up this {name}",
    "Get the details of a specific {name}",
    "Show me this {name}'s details",
    "Fetch the {name} record",
]

CREATE_TEMPLATES = [
    "Create a new {name}",
    "Set up a {name}",
    "Add a new {name}",
    "Register a {name}",
]

UPDATE_TEMPLATES = [
    "Update this {name}",
    "Modify the {name}",
    "Change the {name} settings",
    "Edit this {name}",
]

DELETE_TEMPLATES = [
    "Delete the {name}",
    "Remove this {name}",
    "Cancel the {name}",
    "Destroy the {name}",
]

NOISY_TEMPLATES = [
    "Something went wrong with a {name}, can you check the {plural}?",
    "I need to investigate {plural}, pull them up",
    "The team is asking about {plural}, can you show them?",
    "There's an issue with a {name}, let me see all of them",
    "Can you check the recent {plural}? Something seems off",
    "A {name} looks wrong, show me the list",
    "We got a complaint about a {name}, list the recent ones",
    "Quick, show me the {plural}, something is urgent",
]

QUESTION_TEMPLATES = [
    "How many {plural} are there?",
    "Are there any {plural}?",
    "What's the status of the {plural}?",
    "Which {plural} are active?",
    "Do we have any {plural}?",
]

SUBRESOURCE_QUESTION_TEMPLATES = [
    "Are there any {child_plural} for this {parent}?",
    "How many {child_plural} does this {parent} have?",
    "What {child_plural} are attached to this {parent}?",
    "Does this {parent} have any {child_plural}?",
]

SUBRESOURCE_NOISY_TEMPLATES = [
    "A customer is asking about their {child_plural} on this {parent}, can you check?",
    "I need to look at the {child_plural} for this {parent}, there might be an issue",
    "Something seems off with the {child_plural} under this {parent}",
]

# ── Synonym mappings (Stripe-specific) ────────────────────────────────

SYNONYMS: list[dict] = [
    {"source": "Platform", "target": "PaymentIntent", "terms": [
        "payments we've received", "incoming payments", "all our payments",
        "payment transactions", "charges received", "payments processed",
    ]},
    {"source": "Platform", "target": "Invoice", "terms": [
        "bills sent to customers", "customer invoices", "billing statements",
        "invoices issued", "all our bills", "billing records",
    ]},
    {"source": "Platform", "target": "Dispute", "terms": [
        "chargebacks we've received", "disputed charges", "payment disputes",
        "contested transactions", "chargeback cases", "disputed payments",
    ]},
    {"source": "Platform", "target": "Payout", "terms": [
        "bank transfers we've sent", "bank payouts", "money sent to bank",
        "outgoing bank transfers", "transfers to our bank", "payout transfers",
    ]},
    {"source": "Platform", "target": "Account", "terms": [
        "marketplace seller accounts", "connected seller accounts",
        "partner accounts", "connected platform accounts", "merchant accounts",
        "registered seller accounts",
    ]},
    {"source": "Platform", "target": "BalanceTransaction", "terms": [
        "money coming in and out", "financial transactions",
        "balance movements", "funds activity", "money flow history",
        "transaction history on the balance",
    ]},
    {"source": "Platform", "target": "Balance", "terms": [
        "how much money we have", "current funds available",
        "account balance", "available funds", "money in the account",
        "total balance right now",
    ]},
    {"source": "Platform", "target": "Refund", "terms": [
        "money returned to customers", "refunded payments",
        "returned charges", "customer refunds", "reversed payments",
        "refund transactions",
    ]},
    {"source": "Customer", "target": "PaymentMethod", "terms": [
        "cards on file for this customer", "saved payment options",
        "customer's saved cards", "payment instruments on file",
        "how this customer pays", "stored payment details",
    ]},
    {"source": "Customer", "target": "Subscription", "terms": [
        "recurring plans for this customer", "active memberships",
        "customer's subscription plans", "recurring billing setups",
        "auto-renewing plans", "customer's active plans",
    ]},
    {"source": "Platform", "target": "Subscription", "terms": [
        "recurring subscriptions", "active subscription plans",
        "all memberships", "ongoing recurring charges",
        "auto-billing setups", "subscription programs",
    ]},
    {"source": "Platform", "target": "Charge", "terms": [
        "credit card charges", "card transactions", "processed charges",
        "card payments collected", "credit card transactions",
        "charges on cards",
    ]},
    {"source": "Platform", "target": "Product", "terms": [
        "items in the catalog", "things we sell", "product catalog",
        "goods and services listed", "available products",
        "catalog items",
    ]},
    {"source": "Platform", "target": "Coupon", "terms": [
        "discount codes", "promotional offers", "active discounts",
        "coupon codes available", "discount vouchers",
        "promotional coupons",
    ]},
    {"source": "Platform", "target": "Price", "terms": [
        "pricing tiers", "price points configured", "pricing options",
        "cost configurations", "product prices set up",
        "price plans available",
    ]},
]

# ── Hard negatives (confusing type groups) ────────────────────────────

HARD_NEGATIVE_GROUPS: list[dict] = [
    {
        "source": "Customer",
        "confusing": {
            "BalanceTransaction": [
                "Show the platform balance transactions for this customer",
                "What are the platform-level balance entries for this customer?",
                "Get the overall balance transactions related to this customer",
            ],
            "CustomerBalanceTransaction": [
                "Show the customer's own balance transactions",
                "What transactions are on this customer's stored balance?",
                "Get the balance ledger entries specific to this customer",
            ],
        },
    },
    {
        "source": "Platform",
        "confusing": {
            "Payout": [
                "Show the payouts sent to our bank account",
                "List the bank payouts we've initiated",
                "What money has been sent to our external bank?",
            ],
            "Transfer": [
                "Show the transfers sent to connected accounts",
                "List transfers to our marketplace sellers",
                "What transfers have we made to partner accounts?",
            ],
        },
    },
    {
        "source": "Platform",
        "confusing": {
            "Subscription": [
                "List all active recurring subscriptions",
                "Show the subscriptions on the platform",
                "What subscriptions are currently running?",
            ],
            "SubscriptionSchedule": [
                "Show the subscription schedules configured",
                "List the scheduled subscription changes",
                "What subscription schedules have been set up?",
            ],
        },
    },
    {
        "source": "Platform",
        "confusing": {
            "Invoice": [
                "List all invoices sent to customers",
                "Show the invoices on the platform",
                "Get all customer invoices",
            ],
            "InvoiceItem": [
                "Show the pending invoice items",
                "List invoice line items that haven't been billed yet",
                "What invoice items are queued?",
            ],
        },
    },
    {
        "source": "Customer",
        "confusing": {
            "PaymentMethod": [
                "Show the payment methods for this customer",
                "What cards does this customer have saved?",
                "List this customer's payment options",
            ],
            "PaymentSource": [
                "Show the legacy payment sources for this customer",
                "List the old-style sources attached to this customer",
                "Get this customer's legacy card sources",
            ],
        },
    },
    {
        "source": "Customer",
        "confusing": {
            "Subscription": [
                "Show this customer's active subscriptions",
                "What plans is this customer subscribed to?",
                "List recurring plans for this customer",
            ],
            "Discount": [
                "Show the discounts applied to this customer",
                "What discounts does this customer have?",
                "List active discount on this customer's account",
            ],
        },
    },
]


# ── Generation ────────────────────────────────────────────────────────


def load_graph():
    with open(HERE / "graph_snapshot.json") as f:
        return json.load(f)


def load_test_queries() -> set[str]:
    from benchmarks.stripe_mcp.queries import QUERIES
    return {q["query"].strip().lower() for q in QUERIES}


def group_tools(graph: dict):
    core_types = set(graph["entity_types"].keys())
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for tool in graph["tools"]:
        for inp in tool["input_types"]:
            for out in tool["output_types"]:
                if inp in core_types and out in core_types:
                    groups[(inp, out)].append(tool)
    return dict(groups)


def infer_method(tool: dict) -> str:
    name = tool["name"].lower()
    if name.startswith("delete"):
        return "delete"
    if name.startswith("post"):
        return "post"
    if name.startswith("get"):
        return "get"
    return "other"


def generate_examples(graph: dict) -> list[dict]:
    entity_types = graph["entity_types"]
    pairs = group_tools(graph)
    examples: list[dict] = []

    for (src, tgt), tools in sorted(pairs.items()):
        tgt_name = entity_name(tgt)
        tgt_plural = entity_plural(tgt)
        src_name = entity_name(src)
        method = infer_method(tools[0])
        is_self_loop = src == tgt

        if src == "Platform" and not is_self_loop:
            for tmpl in PLATFORM_LIST_TEMPLATES:
                examples.append({
                    "query": tmpl.format(plural=tgt_plural, name=tgt_name),
                    "source_type": src,
                    "target_type": tgt,
                    "style": "template",
                })
            for tmpl in random.sample(QUESTION_TEMPLATES, min(3, len(QUESTION_TEMPLATES))):
                examples.append({
                    "query": tmpl.format(plural=tgt_plural, name=tgt_name),
                    "source_type": src,
                    "target_type": tgt,
                    "style": "question",
                })
            for tmpl in random.sample(NOISY_TEMPLATES, min(3, len(NOISY_TEMPLATES))):
                examples.append({
                    "query": tmpl.format(plural=tgt_plural, name=tgt_name),
                    "source_type": src,
                    "target_type": tgt,
                    "style": "noisy",
                })

        elif src != "Platform" and not is_self_loop:
            for tmpl in SUBRESOURCE_TEMPLATES:
                examples.append({
                    "query": tmpl.format(
                        parent=src_name, child_plural=tgt_plural, child_name=tgt_name,
                    ),
                    "source_type": src,
                    "target_type": tgt,
                    "style": "template",
                })
            for tmpl in random.sample(SUBRESOURCE_QUESTION_TEMPLATES,
                                       min(2, len(SUBRESOURCE_QUESTION_TEMPLATES))):
                examples.append({
                    "query": tmpl.format(parent=src_name, child_plural=tgt_plural),
                    "source_type": src,
                    "target_type": tgt,
                    "style": "question",
                })
            for tmpl in random.sample(SUBRESOURCE_NOISY_TEMPLATES,
                                       min(2, len(SUBRESOURCE_NOISY_TEMPLATES))):
                examples.append({
                    "query": tmpl.format(parent=src_name, child_plural=tgt_plural),
                    "source_type": src,
                    "target_type": tgt,
                    "style": "noisy",
                })

        if is_self_loop:
            if method == "get":
                for tmpl in RETRIEVE_TEMPLATES:
                    examples.append({
                        "query": tmpl.format(name=tgt_name, plural=tgt_plural),
                        "source_type": src,
                        "target_type": tgt,
                        "style": "template",
                    })
            elif method == "post":
                has_id = any("{" in p for p in tools[0].get("path", "").split("/"))
                if has_id or "update" in tools[0].get("description", "").lower():
                    for tmpl in UPDATE_TEMPLATES:
                        examples.append({
                            "query": tmpl.format(name=tgt_name),
                            "source_type": src,
                            "target_type": tgt,
                            "style": "template",
                        })
                else:
                    for tmpl in CREATE_TEMPLATES:
                        examples.append({
                            "query": tmpl.format(name=tgt_name),
                            "source_type": src,
                            "target_type": tgt,
                            "style": "template",
                        })
            elif method == "delete":
                for tmpl in DELETE_TEMPLATES:
                    examples.append({
                        "query": tmpl.format(name=tgt_name),
                        "source_type": src,
                        "target_type": tgt,
                        "style": "template",
                    })

    return examples


def generate_synonyms() -> list[dict]:
    examples = []
    for syn in SYNONYMS:
        for term in syn["terms"]:
            examples.append({
                "query": f"Show me {term}",
                "source_type": syn["source"],
                "target_type": syn["target"],
                "style": "synonym",
            })
            examples.append({
                "query": f"List {term}",
                "source_type": syn["source"],
                "target_type": syn["target"],
                "style": "synonym",
            })
    return examples


def generate_hard_negatives() -> list[dict]:
    examples = []
    for group in HARD_NEGATIVE_GROUPS:
        src = group["source"]
        for tgt, queries in group["confusing"].items():
            for q in queries:
                examples.append({
                    "query": q,
                    "source_type": src,
                    "target_type": tgt,
                    "style": "hard_negative",
                })
    return examples


def main():
    random.seed(42)

    graph = load_graph()
    test_queries = load_test_queries()
    entity_types = graph["entity_types"]

    print(f"Graph: {len(graph['tools'])} tools, {len(entity_types)} entity types")
    print(f"Test queries (held out): {len(test_queries)}")

    all_examples = []
    all_examples.extend(generate_examples(graph))
    all_examples.extend(generate_synonyms())
    all_examples.extend(generate_hard_negatives())

    print(f"\nRaw examples: {len(all_examples)}")

    # Deduplicate and filter test queries
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

    print(f"After dedup: {len(filtered)}")
    if test_overlap:
        print(f"Removed {test_overlap} test query overlaps")

    random.shuffle(filtered)

    # Coverage check
    sources = {ex["source_type"] for ex in filtered}
    targets = {ex["target_type"] for ex in filtered}
    all_types = sources | targets
    missing = set(entity_types.keys()) - all_types
    print(f"\nType coverage: {len(all_types)} / {len(entity_types)}")
    if missing:
        print(f"Missing types ({len(missing)}): {sorted(missing)[:20]}...")

    # Style distribution
    from collections import Counter
    styles = Counter(ex["style"] for ex in filtered)
    print(f"\nStyle distribution:")
    for style, count in styles.most_common():
        print(f"  {style}: {count}")

    # Write
    out_path = HERE / "training_data.jsonl"
    with open(out_path, "w") as f:
        for ex in filtered:
            f.write(json.dumps(ex) + "\n")

    print(f"\nWritten {len(filtered)} examples to {out_path}")


if __name__ == "__main__":
    main()
