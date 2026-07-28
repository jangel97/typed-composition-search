"""TCS registry built from the Stripe OpenAPI spec."""

from __future__ import annotations

from pathlib import Path

from typed_composition_search import Registry

from .openapi_parser import collect_entity_types, parse_spec

DEFAULT_SPEC = Path("/tmp/stripe_spec3.json")


def build_registry(spec_path: Path | str = DEFAULT_SPEC) -> Registry:
    ops = parse_spec(spec_path)

    reg = Registry()
    for op in ops:
        reg.register(
            op.full_name,
            op.input_types,
            op.output_types,
            op.description,
        )

    return reg


def _build_entity_types(spec_path: Path | str = DEFAULT_SPEC) -> dict[str, str]:
    ops = parse_spec(spec_path)
    all_types = collect_entity_types(ops)

    all_types["Platform"] = "The Stripe platform root (starting point for listing resources)"
    return all_types


ENTITY_TYPES = _build_entity_types()
