"""Parse the Stripe OpenAPI spec into typed tool edges.

Reads spec3.json from stripe/openapi and extracts operations with inferred
input/output entity types for building a typed composition graph.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedOperation:
    operation_id: str
    method: str
    path: str
    description: str
    input_types: tuple[str, ...]
    output_types: tuple[str, ...]
    response_schema_ref: str | None = None

    @property
    def full_name(self) -> str:
        return self.operation_id


def _singularize(name: str) -> str:
    """Naive singularization for API resource names."""
    if name.endswith("ies"):
        return name[:-3] + "y"
    if name.endswith("ses"):
        return name[:-2]
    if name.endswith("s") and not name.endswith("ss"):
        return name[:-1]
    return name


def _to_pascal(name: str) -> str:
    """Convert snake_case or dot.case to PascalCase entity name."""
    name = name.replace(".", "_")
    return "".join(word.capitalize() for word in name.split("_"))


def _ref_to_entity(ref: str) -> str:
    """Convert a schema ref like 'payment_intent' to 'PaymentIntent'."""
    if ref.startswith("deleted_"):
        return "DeletionResult"
    return _to_pascal(ref)


SKIP_PREFIXES = [
    "/v1/test_helpers/",
]

SKIP_SUFFIXES = [
    "/search",
]


def _should_skip(path: str, operation_id: str) -> bool:
    for prefix in SKIP_PREFIXES:
        if path.startswith(prefix):
            return True
    for suffix in SKIP_SUFFIXES:
        if path.endswith(suffix):
            return True
    return False


def _get_response_ref(details: dict) -> str | None:
    responses = details.get("responses", {})
    for code in ("200", "201", "202"):
        if code not in responses:
            continue
        content = responses[code].get("content", {}).get("application/json", {})
        schema = content.get("schema", {})
        ref = schema.get("$ref", "")
        if ref:
            return ref.rsplit("/", 1)[-1]
        # Check for list pattern: {data: {items: {$ref}}}
        props = schema.get("properties", {})
        if "data" in props:
            items = props["data"].get("items", {})
            item_ref = items.get("$ref", "")
            if item_ref:
                return "list<" + item_ref.rsplit("/", 1)[-1] + ">"
    return None


def _infer_types_from_path(
    path: str, method: str, response_ref: str | None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Infer (input_types, output_types) from path structure and response ref."""
    parts = path.strip("/").split("/")
    parts = parts[1:]  # strip 'v1'

    # Separate resource segments from {id} placeholders
    resources = []
    has_id = []
    for p in parts:
        if p.startswith("{"):
            has_id.append(True)
        else:
            resources.append(p)
            has_id.append(False)

    if not resources:
        return ("Platform",), ("Platform",)

    # Determine the output entity from the response ref
    output_entity = None
    is_list = False
    if response_ref:
        if response_ref.startswith("list<"):
            inner = response_ref[5:-1]
            output_entity = _ref_to_entity(inner)
            is_list = True
        elif response_ref.startswith("deleted_"):
            output_entity = "DeletionResult"
        else:
            output_entity = _ref_to_entity(response_ref)

    # Determine parent entity from path
    # Singularize if an {id} follows the resource (we're referring to one instance)
    parent_resource = resources[0]
    first_segment_has_id = len(parts) > 1 and parts[1].startswith("{") if len(parts) > 1 else False
    if first_segment_has_id:
        parent_entity = _to_pascal(_singularize(parent_resource))
    else:
        parent_entity = _to_pascal(parent_resource)

    # Check if this is a sub-resource (e.g., /customers/{id}/sources)
    is_sub_resource = len(resources) >= 2 and any(has_id)

    if is_sub_resource:
        # Parent is the first resource, we know it by ID
        input_entity = parent_entity
        if output_entity is None:
            child_resource = resources[-1]
            # Singularize child unless the last part has an {id} after it
            last_part_idx = path.rstrip("/").split("/").index("{" if False else resources[-1])
            output_entity = _to_pascal(_singularize(child_resource))
        return (input_entity,), (output_entity,)

    # Top-level resource
    if method == "get":
        # Check if it's a list (no {id} at end) or retrieve (has {id})
        last_is_id = path.rstrip("/").endswith("}")
        if last_is_id:
            # Retrieve: EntityId -> Entity
            if output_entity is None:
                output_entity = parent_entity
            return (parent_entity,), (output_entity,)
        else:
            # List: Platform -> Entity
            if output_entity is None:
                output_entity = parent_entity
            return ("Platform",), (output_entity,)

    if method == "post":
        last_is_id = path.rstrip("/").endswith("}")
        if last_is_id:
            # Update: Entity -> Entity
            if output_entity is None:
                output_entity = parent_entity
            return (parent_entity,), (output_entity,)
        else:
            # Create: Platform -> Entity
            if output_entity is None:
                output_entity = parent_entity
            return ("Platform",), (output_entity,)

    if method == "delete":
        return (parent_entity,), ("DeletionResult",)

    if output_entity is None:
        output_entity = parent_entity
    return (parent_entity,), (output_entity,)


def _get_description(details: dict) -> str:
    return details.get("summary", "") or details.get("description", "")[:120] or ""


def parse_spec(spec_path: str | Path) -> list[ParsedOperation]:
    with open(spec_path) as f:
        spec = json.load(f)

    operations: list[ParsedOperation] = []

    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue

            operation_id = details.get("operationId", "")
            if not operation_id:
                continue

            if _should_skip(path, operation_id):
                continue

            response_ref = _get_response_ref(details)
            input_types, output_types = _infer_types_from_path(
                path, method, response_ref
            )

            operations.append(ParsedOperation(
                operation_id=operation_id,
                method=method,
                path=path,
                description=_get_description(details),
                input_types=input_types,
                output_types=output_types,
                response_schema_ref=response_ref,
            ))

    return operations


def collect_entity_types(operations: list[ParsedOperation]) -> dict[str, str]:
    entities: set[str] = set()
    for op in operations:
        entities.update(op.input_types)
        entities.update(op.output_types)

    skip = {"DeletionResult", "Platform"}
    structural_suffixes = ("Name", "Spec")

    type_descriptions: dict[str, str] = {}
    for e in sorted(entities):
        if e in skip:
            continue
        if e.endswith(structural_suffixes):
            continue
        type_descriptions[e] = _describe_entity(e)

    return type_descriptions


DESCRIPTIONS: dict[str, str] = {
    "Account": "A Stripe connected account",
    "AccountLink": "A link for onboarding a connected account",
    "AccountSession": "A session for embedded account management",
    "ApplePayDomain": "A verified Apple Pay domain",
    "ApplicationFee": "A fee collected from a connected account",
    "AppsSecret": "An app secret for Stripe Apps",
    "Balance": "The account balance (available, pending funds)",
    "BalanceTransaction": "A transaction that affected the balance",
    "BankAccount": "A bank account payment method",
    "BillingAlert": "A billing usage alert",
    "BillingCreditBalanceTransaction": "A credit balance transaction",
    "BillingCreditGrant": "A credit grant for billing",
    "BillingMeter": "A usage meter for billing",
    "BillingMeterEvent": "A usage event recorded by a meter",
    "BillingMeterEventAdjustment": "An adjustment to a meter event",
    "BillingMeterEventSummary": "A summary of meter events",
    "BillingPortalConfiguration": "A customer billing portal configuration",
    "BillingPortalSession": "A customer billing portal session",
    "Capability": "A capability of a connected account",
    "Card": "A card payment method",
    "CashBalance": "A customer's cash balance",
    "CashBalanceTransaction": "A transaction on a customer's cash balance",
    "Charge": "A credit card charge",
    "CheckoutSession": "A Checkout session for collecting payments",
    "CheckoutSessionLineItem": "A line item in a Checkout session",
    "ClimateOrder": "A carbon removal order",
    "ClimateProduct": "A carbon removal product",
    "ClimateSupplier": "A carbon removal supplier",
    "ConfirmationToken": "A confirmation token for payment",
    "CountrySpec": "Country-specific requirements for accounts",
    "Coupon": "A discount coupon",
    "CreditNote": "A credit note on an invoice",
    "CreditNoteLine": "A line item on a credit note",
    "Customer": "A Stripe customer",
    "CustomerBalanceTransaction": "A transaction on a customer's balance",
    "Discount": "A discount applied to a customer or subscription",
    "Dispute": "A charge dispute (chargeback)",
    "EntitlementsActiveEntitlement": "An active product entitlement",
    "EntitlementsFeature": "A product feature for entitlements",
    "EphemeralKey": "A short-lived API key for client-side operations",
    "Event": "A webhook event",
    "ExchangeRate": "A currency exchange rate",
    "ExternalAccount": "An external account (bank or card) on a connected account",
    "FeeRefund": "A refund of an application fee",
    "File": "An uploaded file (identity documents, disputes, etc.)",
    "FileLink": "A shareable link to a file",
    "FinancialConnectionsAccount": "A linked financial account",
    "FinancialConnectionsSession": "A session for linking financial accounts",
    "FinancialConnectionsTransaction": "A transaction from a linked account",
    "ForwardingRequest": "A forwarded API request",
    "IdentityVerificationReport": "An identity verification report",
    "IdentityVerificationSession": "An identity verification session",
    "Invoice": "An invoice for a customer",
    "InvoiceItem": "A line item on an invoice",
    "InvoiceLineItem": "A line on an invoice",
    "InvoiceRenderingTemplate": "A template for rendering invoices",
    "IssuingAuthorization": "An Issuing card authorization",
    "IssuingCard": "An Issuing card",
    "IssuingCardholder": "An Issuing cardholder",
    "IssuingDispute": "An Issuing dispute",
    "IssuingPersonalizationDesign": "An Issuing card personalization design",
    "IssuingPhysicalBundle": "An Issuing physical card bundle",
    "IssuingSettlement": "An Issuing settlement",
    "IssuingToken": "An Issuing digital wallet token",
    "IssuingTransaction": "An Issuing transaction",
    "Item": "A subscription item",
    "LineItem": "A line item (quote or invoice)",
    "LinkedAccountsAccount": "A linked financial account (legacy)",
    "LoginLink": "A login link for a connected account",
    "Mandate": "A mandate for recurring payments",
    "PaymentIntent": "A payment intent (tracks payment lifecycle)",
    "PaymentLink": "A payment link for collecting payments",
    "PaymentMethod": "A payment method (card, bank, etc.)",
    "PaymentMethodConfiguration": "A payment method configuration",
    "PaymentMethodDomain": "A domain for payment method display",
    "PaymentRecord": "A record of a payment",
    "PaymentSource": "A payment source (card, bank account)",
    "Payout": "A payout to an external account",
    "Person": "A person associated with a connected account",
    "Plan": "A subscription plan (legacy, see Price)",
    "Price": "A price for a product",
    "Product": "A product or service",
    "ProductFeature": "A feature of a product",
    "PromotionCode": "A promotion code for a coupon",
    "Quote": "A quote for a customer",
    "QuoteLine": "A line on a quote",
    "RadarEarlyFraudWarning": "An early fraud warning from Radar",
    "RadarValueList": "A Radar value list for fraud rules",
    "RadarValueListItem": "An item in a Radar value list",
    "Refund": "A refund of a charge",
    "ReportingReportRun": "A report run",
    "ReportingReportType": "A type of report available",
    "Review": "A review of a payment",
    "ScheduledQueryRun": "A scheduled Sigma query run",
    "SetupAttempt": "An attempt to set up a payment method",
    "SetupIntent": "A setup intent for saving payment methods",
    "ShippingRate": "A shipping rate",
    "SigmaScheduledQueryRun": "A Sigma scheduled query run",
    "Source": "A payment source (legacy)",
    "SourceTransaction": "A transaction on a source",
    "Subscription": "A recurring subscription",
    "SubscriptionItem": "An item in a subscription",
    "SubscriptionSchedule": "A subscription schedule",
    "TaxCalculation": "A tax calculation",
    "TaxCalculationLineItem": "A line item in a tax calculation",
    "TaxId": "A tax ID for a customer",
    "TaxRate": "A tax rate",
    "TaxRegistration": "A tax registration",
    "TaxSettings": "Tax settings for the account",
    "TaxTransaction": "A tax transaction",
    "TaxTransactionLineItem": "A line item in a tax transaction",
    "TerminalConfiguration": "A Terminal reader configuration",
    "TerminalConnectionToken": "A Terminal connection token",
    "TerminalLocation": "A Terminal reader location",
    "TerminalReader": "A Terminal card reader device",
    "Token": "A single-use token representing payment details",
    "Topup": "A top-up of the Stripe balance",
    "Transfer": "A transfer to a connected account",
    "TransferReversal": "A reversal of a transfer",
    "TreasuryAccount": "A Treasury financial account",
    "TreasuryCreditReversal": "A Treasury credit reversal",
    "TreasuryDebitReversal": "A Treasury debit reversal",
    "TreasuryFinancialAccount": "A Treasury financial account",
    "TreasuryFinancialAccountFeatures": "Features of a Treasury financial account",
    "TreasuryInboundTransfer": "A Treasury inbound transfer",
    "TreasuryOutboundPayment": "A Treasury outbound payment",
    "TreasuryOutboundTransfer": "A Treasury outbound transfer",
    "TreasuryReceivedCredit": "A Treasury received credit",
    "TreasuryReceivedDebit": "A Treasury received debit",
    "TreasuryTransaction": "A Treasury transaction",
    "TreasuryTransactionEntry": "A Treasury transaction entry",
    "UsageRecord": "A usage record for metered billing",
    "UsageRecordSummary": "A summary of usage records",
    "WebhookEndpoint": "A webhook endpoint for receiving events",
}


def _describe_entity(name: str) -> str:
    if name in DESCRIPTIONS:
        return DESCRIPTIONS[name]
    return f"A Stripe {' '.join(re.findall(r'[A-Z][a-z]*', name)).lower()} resource"


if __name__ == "__main__":
    import sys
    spec_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/stripe_spec3.json"

    ops = parse_spec(spec_path)
    entity_types = collect_entity_types(ops)

    print(f"Total operations: {len(ops)}")
    print(f"Entity types: {len(entity_types)}")

    print(f"\nSample operations:")
    for op in ops[:20]:
        print(f"  {op.full_name}: {op.input_types} -> {op.output_types}  [{op.method.upper()} {op.path}]")

    print(f"\nEntity types ({len(entity_types)}):")
    for name, desc in sorted(entity_types.items()):
        print(f"  {name}: {desc}")
