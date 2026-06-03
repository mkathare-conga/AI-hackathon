"""
Quote-to-Contract Drift Detector — service layer.

Compares structured quote data with AI-extracted contract facts
to detect commercial mismatches (drift) between what was sold and what was signed.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date

import psycopg
from psycopg.rows import dict_row

from app.config import get_ai_settings, get_data_settings
from app.models_drift import (
    DriftContract,
    DriftDashboard,
    DriftFinding,
    DriftSummary,
    Quote,
    QuoteLine,
)

LOGGER = logging.getLogger(__name__)


# ─── Database helpers ─────────────────────────────────────────────────────────

def _conn():
    settings = get_data_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured")
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


# ─── Data access ──────────────────────────────────────────────────────────────

def list_quotes() -> list[Quote]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM quotes ORDER BY created_date DESC")
            return [Quote(**row) for row in cur.fetchall()]


def get_quote(quote_id: str) -> Quote | None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM quotes WHERE quote_id = %s", (quote_id,))
            row = cur.fetchone()
            return Quote(**row) if row else None


def get_quote_lines(quote_id: str) -> list[QuoteLine]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM quote_lines WHERE quote_id = %s ORDER BY line_id", (quote_id,))
            return [QuoteLine(**row) for row in cur.fetchall()]


def list_drift_contracts() -> list[DriftContract]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM drift_contracts ORDER BY signed_date DESC")
            return [DriftContract(**row) for row in cur.fetchall()]


def get_drift_contract(contract_id: str) -> DriftContract | None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM drift_contracts WHERE contract_id = %s", (contract_id,))
            row = cur.fetchone()
            return DriftContract(**row) if row else None


def get_drift_contract_for_quote(quote_id: str) -> DriftContract | None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM drift_contracts WHERE quote_id = %s LIMIT 1", (quote_id,))
            row = cur.fetchone()
            return DriftContract(**row) if row else None


def list_findings(quote_id: str | None = None) -> list[DriftFinding]:
    with _conn() as conn:
        with conn.cursor() as cur:
            if quote_id:
                cur.execute("SELECT * FROM drift_findings WHERE quote_id = %s ORDER BY severity, finding_id", (quote_id,))
            else:
                cur.execute("SELECT * FROM drift_findings ORDER BY severity, finding_id")
            return [DriftFinding(**row) for row in cur.fetchall()]


def get_finding(finding_id: str) -> DriftFinding | None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM drift_findings WHERE finding_id = %s", (finding_id,))
            row = cur.fetchone()
            return DriftFinding(**row) if row else None


# ─── AI extraction ────────────────────────────────────────────────────────────

def _chat_completion_json(system_prompt: str, user_prompt: str) -> dict | None:
    """Call the same AI backend used by the leakage agent."""
    import json as _json
    import re
    from urllib import error, request

    settings = get_ai_settings()
    if not settings.enabled:
        return None

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    if settings.model:
        payload["model"] = settings.model

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.api_key}",
    }
    if settings.provider == "github-models":
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2026-03-10"
    else:
        headers["api-key"] = settings.api_key

    http_request = request.Request(
        settings.chat_completions_url,
        data=_json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=settings.timeout_seconds) as response:
            result = _json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, _json.JSONDecodeError) as exc:
        LOGGER.warning("AI request failed for drift extraction: %s", exc)
        return None

    content = result.get("choices", [{}])[0].get("message", {}).get("content")
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    if not isinstance(content, str):
        return None

    try:
        return _json.loads(content)
    except _json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return _json.loads(match.group(0))
            except _json.JSONDecodeError:
                pass
    return None


def _extract_contract_facts_with_ai(contract_text: str, quote_lines: list[QuoteLine]) -> list[dict] | None:
    """Use AI to extract commercial facts from contract text, guided by quote attributes."""
    line_summaries = []
    for line in quote_lines:
        line_summaries.append({
            "product_name": line.product_name,
            "quantity": line.quantity,
            "unit_price": line.unit_price,
            "discount_percent": line.discount_percent,
            "support_tier": line.support_tier,
            "renewal_uplift_percent": line.renewal_uplift_percent,
            "payment_terms_days": line.payment_terms_days,
        })

    response = _chat_completion_json(
        system_prompt=(
            "You extract commercial facts from signed contracts and compare them to quote data. "
            "For each quote line item, find the corresponding terms in the contract text. "
            "Return strict JSON with key 'contract_facts' containing an array of objects. "
            "Each object must have: product_name, quantity, unit_price, discount_percent, "
            "support_tier, renewal_uplift_percent, payment_terms_days, source_clause_text. "
            "Use null for any attribute not mentioned in the contract. "
            "source_clause_text should be the relevant excerpt from the contract."
        ),
        user_prompt=(
            "Extract the commercial facts from this signed contract that correspond to these quote line items.\n\n"
            f"QUOTE LINE ITEMS:\n{json.dumps(line_summaries, indent=2)}\n\n"
            f"SIGNED CONTRACT TEXT:\n{contract_text}"
        ),
    )
    if response and "contract_facts" in response:
        return response["contract_facts"]
    return None


def _extract_contract_facts_deterministic(contract_text: str, quote_lines: list[QuoteLine]) -> list[dict]:
    """Regex/heuristic fallback for extracting contract facts without AI."""
    import re

    facts = []
    text_lower = contract_text.lower()

    for line in quote_lines:
        fact: dict = {
            "product_name": line.product_name,
            "quantity": None,
            "unit_price": None,
            "discount_percent": None,
            "support_tier": None,
            "renewal_uplift_percent": None,
            "payment_terms_days": None,
            "source_clause_text": None,
        }

        # Try to find quantity for this product
        product_pattern = re.escape(line.product_name)
        qty_match = re.search(
            rf"{product_pattern}[^.]*?(\d[\d,]*)\s*(?:seats?|subscriptions?|users?|licenses?)",
            contract_text, re.IGNORECASE
        )
        if qty_match:
            fact["quantity"] = int(qty_match.group(1).replace(",", ""))
            fact["source_clause_text"] = qty_match.group(0).strip()

        # Try to find unit price
        price_match = re.search(
            rf"{product_pattern}[^.]*?\$\s*([\d,]+\.?\d*)\s*per\s*(?:seat|user|subscription)",
            contract_text, re.IGNORECASE
        )
        if price_match:
            fact["unit_price"] = float(price_match.group(1).replace(",", ""))

        # Find payment terms
        payment_match = re.search(r"net\s+(\d+)\s*days?", contract_text, re.IGNORECASE)
        if payment_match:
            fact["payment_terms_days"] = int(payment_match.group(1))

        # Find renewal/uplift
        uplift_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:annual|yearly|per annum|annually)", contract_text, re.IGNORECASE)
        if uplift_match:
            fact["renewal_uplift_percent"] = float(uplift_match.group(1))

        # Find support tier
        if "premium support" in text_lower or "24/7" in text_lower:
            if "not included" in text_lower or "separate" in text_lower:
                fact["support_tier"] = "standard"
            else:
                fact["support_tier"] = "premium"
        elif "standard support" in text_lower or "business hours" in text_lower or "business-hours" in text_lower:
            fact["support_tier"] = "standard"

        facts.append(fact)

    return facts


# ─── Drift comparison ─────────────────────────────────────────────────────────

_SEVERITY_MAP = {
    "quantity": "high",
    "unit_price": "high",
    "renewal_uplift_percent": "high",
    "payment_terms_days": "medium",
    "support_tier": "medium",
    "scope": "high",
}

_DRIFT_TYPE_MAP = {
    "quantity": "quantity",
    "unit_price": "price",
    "renewal_uplift_percent": "renewal_terms",
    "payment_terms_days": "payment_terms",
    "support_tier": "support",
}


def _compute_annual_impact(
    attribute: str,
    quote_line: QuoteLine,
    quote_value,
    contract_value,
) -> float | None:
    """Estimate annual revenue impact of a drift finding."""
    if attribute == "quantity" and contract_value is not None:
        lost_seats = quote_line.quantity - int(contract_value)
        if lost_seats > 0:
            effective_price = quote_line.unit_price * (1 - quote_line.discount_percent / 100)
            return round(lost_seats * effective_price * 12, 2)
    elif attribute == "unit_price" and contract_value is not None:
        price_diff = (quote_line.unit_price * (1 - quote_line.discount_percent / 100)) - float(contract_value)
        if price_diff > 0:
            return round(price_diff * quote_line.quantity * 12, 2)
    elif attribute == "renewal_uplift_percent" and contract_value is not None and quote_line.renewal_uplift_percent:
        uplift_diff = quote_line.renewal_uplift_percent - float(contract_value)
        if uplift_diff > 0:
            effective_price = quote_line.unit_price * (1 - quote_line.discount_percent / 100)
            monthly_revenue = effective_price * quote_line.quantity
            return round(monthly_revenue * 12 * (uplift_diff / 100), 2)
    return None


def _generate_explanation(
    attribute: str,
    product_name: str,
    quote_value,
    contract_value,
    impact: float | None,
) -> str:
    """Generate a plain-language explanation for a drift finding."""
    explanations = {
        "quantity": (
            f"The quote approved {quote_value} seats for {product_name}, "
            f"but the signed contract only includes {contract_value} seats. "
            + (f"This represents approximately {_fmt_money(impact)} in lost annual revenue." if impact else "")
        ),
        "unit_price": (
            f"The effective price for {product_name} changed from "
            f"${quote_value}/seat/month in the quote to ${contract_value}/seat/month in the contract."
            + (f" Annual impact: {_fmt_money(impact)}." if impact else "")
        ),
        "renewal_uplift_percent": (
            f"The renewal uplift for {product_name} was quoted at {quote_value}% annually, "
            f"but the contract caps it at {contract_value}%. "
            + (f"This weakens future pricing by approximately {_fmt_money(impact)} per year." if impact else "")
        ),
        "payment_terms_days": (
            f"Payment terms extended from net {quote_value} days (quoted) to "
            f"net {contract_value} days (signed). This delays cash collection and increases working capital requirements."
        ),
        "support_tier": (
            f"The quote included {quote_value} support for {product_name}, "
            f"but the contract specifies {contract_value} support. "
            "This reduces the service commitment without a corresponding price reduction."
        ),
        "scope": (
            f"{product_name} was included in the quote but is absent or excluded "
            f"from the signed contract. The entire line item value is at risk."
        ),
    }
    return explanations.get(attribute, f"{attribute} changed from {quote_value} to {contract_value}.")


def _fmt_money(value: float | None) -> str:
    if value is None:
        return "$0"
    return f"${value:,.0f}"


def _compare_line(quote_line: QuoteLine, contract_fact: dict) -> list[DriftFinding]:
    """Compare a single quote line against its extracted contract facts."""
    findings: list[DriftFinding] = []

    comparisons = [
        ("quantity", quote_line.quantity, contract_fact.get("quantity")),
        ("unit_price",
         round(quote_line.unit_price * (1 - quote_line.discount_percent / 100), 2),
         contract_fact.get("unit_price")),
        ("renewal_uplift_percent", quote_line.renewal_uplift_percent, contract_fact.get("renewal_uplift_percent")),
        ("payment_terms_days", quote_line.payment_terms_days, contract_fact.get("payment_terms_days")),
        ("support_tier", quote_line.support_tier, contract_fact.get("support_tier")),
    ]

    for attribute, quote_value, contract_value in comparisons:
        if quote_value is None or contract_value is None:
            continue
        # Normalize for comparison
        qv = str(quote_value).lower().strip()
        cv = str(contract_value).lower().strip()
        if qv == cv:
            continue

        # Check if this is actually worse for the seller
        is_drift = False
        if attribute == "quantity" and int(contract_value) < int(quote_value):
            is_drift = True
        elif attribute == "unit_price" and float(contract_value) < float(quote_value):
            is_drift = True
        elif attribute == "renewal_uplift_percent" and float(contract_value) < float(quote_value):
            is_drift = True
        elif attribute == "payment_terms_days" and int(contract_value) > int(quote_value):
            is_drift = True
        elif attribute == "support_tier" and qv != cv:
            # Downgrade is drift
            tier_rank = {"premium": 2, "standard": 1, "basic": 0}
            if tier_rank.get(cv, 0) < tier_rank.get(qv, 0):
                is_drift = True

        if not is_drift:
            continue

        impact = _compute_annual_impact(attribute, quote_line, quote_value, contract_value)
        explanation = _generate_explanation(
            attribute, quote_line.product_name, quote_value, contract_value, impact
        )

        findings.append(DriftFinding(
            finding_id=f"drift-{_short_id()}",
            quote_id=quote_line.quote_id,
            contract_id="",  # filled by caller
            drift_type=_DRIFT_TYPE_MAP.get(attribute, "scope"),
            attribute_name=attribute,
            quote_value=str(quote_value),
            contract_value=str(contract_value),
            severity=_SEVERITY_MAP.get(attribute, "medium"),
            estimated_annual_impact=impact,
            explanation=explanation,
            source_clause_text=contract_fact.get("source_clause_text"),
            confidence_score=0.92 if contract_fact.get("source_clause_text") else 0.75,
        ))

    return findings


def _check_scope_drift(quote_lines: list[QuoteLine], contract_facts: list[dict]) -> list[DriftFinding]:
    """Check if any quoted products are entirely missing from the contract."""
    findings: list[DriftFinding] = []
    contract_products = {
        fact.get("product_name", "").lower()
        for fact in contract_facts
        if fact.get("quantity") is not None or fact.get("unit_price") is not None
    }

    for line in quote_lines:
        if line.product_name.lower() not in contract_products:
            # Check if it's a service that might be intentionally excluded
            effective_price = line.unit_price * (1 - line.discount_percent / 100)
            annual_value = effective_price * line.quantity * 12

            findings.append(DriftFinding(
                finding_id=f"drift-{_short_id()}",
                quote_id=line.quote_id,
                contract_id="",
                drift_type="scope",
                attribute_name="scope",
                quote_value=f"{line.product_name} ({line.quantity} units)",
                contract_value="Not found in contract",
                severity="high",
                estimated_annual_impact=round(annual_value, 2),
                explanation=_generate_explanation(
                    "scope", line.product_name, line.product_name, "absent", annual_value
                ),
                source_clause_text=None,
                confidence_score=0.85,
            ))

    return findings


# ─── Main analysis orchestrator ───────────────────────────────────────────────

def run_drift_analysis(quote_id: str, contract_id: str) -> DriftSummary:
    """Run full drift analysis comparing a quote to a signed contract."""
    quote = get_quote(quote_id)
    if quote is None:
        raise ValueError(f"Quote {quote_id} not found")

    contract = get_drift_contract(contract_id)
    if contract is None:
        raise ValueError(f"Contract {contract_id} not found")

    quote_lines = get_quote_lines(quote_id)
    if not quote_lines:
        raise ValueError(f"No quote lines found for {quote_id}")

    # Extract contract facts (AI-first, deterministic fallback)
    contract_facts = _extract_contract_facts_with_ai(contract.contract_text, quote_lines)
    if contract_facts is None:
        LOGGER.info("AI extraction unavailable, using deterministic fallback for drift analysis")
        contract_facts = _extract_contract_facts_deterministic(contract.contract_text, quote_lines)

    # Compare each quote line to its contract counterpart
    all_findings: list[DriftFinding] = []

    for i, quote_line in enumerate(quote_lines):
        if i < len(contract_facts):
            line_findings = _compare_line(quote_line, contract_facts[i])
            for finding in line_findings:
                finding.contract_id = contract_id
            all_findings.extend(line_findings)

    # Check for scope drift (products missing from contract)
    scope_findings = _check_scope_drift(quote_lines, contract_facts)
    for finding in scope_findings:
        finding.contract_id = contract_id
    all_findings.extend(scope_findings)

    # Persist findings
    _persist_findings(all_findings)

    # Build summary
    high_count = sum(1 for f in all_findings if f.severity == "high")
    medium_count = sum(1 for f in all_findings if f.severity == "medium")
    low_count = sum(1 for f in all_findings if f.severity == "low")
    total_impact = sum(f.estimated_annual_impact or 0 for f in all_findings)

    return DriftSummary(
        quote_id=quote_id,
        contract_id=contract_id,
        account_name=quote.account_name,
        opportunity_name=quote.opportunity_name,
        total_findings=len(all_findings),
        high_severity_count=high_count,
        medium_severity_count=medium_count,
        low_severity_count=low_count,
        total_estimated_annual_impact=round(total_impact, 2),
        findings=all_findings,
    )


def _persist_findings(findings: list[DriftFinding]) -> None:
    """Save drift findings to the database."""
    if not findings:
        return
    with _conn() as conn:
        with conn.cursor() as cur:
            for f in findings:
                cur.execute(
                    """
                    INSERT INTO drift_findings
                        (finding_id, quote_id, contract_id, drift_type, attribute_name,
                         quote_value, contract_value, severity, estimated_annual_impact,
                         explanation, source_clause_text, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (finding_id) DO NOTHING
                    """,
                    (f.finding_id, f.quote_id, f.contract_id, f.drift_type, f.attribute_name,
                     f.quote_value, f.contract_value, f.severity, f.estimated_annual_impact,
                     f.explanation, f.source_clause_text, f.confidence_score),
                )
            conn.commit()


# ─── Dashboard ────────────────────────────────────────────────────────────────

def get_drift_dashboard() -> DriftDashboard:
    """Get overall drift analysis dashboard."""
    quotes = list_quotes()
    all_analyses: list[DriftSummary] = []

    for quote in quotes:
        contract = get_drift_contract_for_quote(quote.quote_id)
        if contract is None:
            continue
        findings = list_findings(quote.quote_id)
        if not findings:
            continue

        high_count = sum(1 for f in findings if f.severity == "high")
        medium_count = sum(1 for f in findings if f.severity == "medium")
        low_count = sum(1 for f in findings if f.severity == "low")
        total_impact = sum(f.estimated_annual_impact or 0 for f in findings)

        all_analyses.append(DriftSummary(
            quote_id=quote.quote_id,
            contract_id=contract.contract_id,
            account_name=quote.account_name,
            opportunity_name=quote.opportunity_name,
            total_findings=len(findings),
            high_severity_count=high_count,
            medium_severity_count=medium_count,
            low_severity_count=low_count,
            total_estimated_annual_impact=round(total_impact, 2),
            findings=findings,
        ))

    return DriftDashboard(
        total_quotes_analyzed=len(all_analyses),
        total_findings=sum(a.total_findings for a in all_analyses),
        total_high_severity=sum(a.high_severity_count for a in all_analyses),
        total_estimated_impact=round(sum(a.total_estimated_annual_impact for a in all_analyses), 2),
        analyses=all_analyses,
    )


def analyze_all_quotes() -> DriftDashboard:
    """Run drift analysis for all quote/contract pairs that don't have findings yet."""
    quotes = list_quotes()
    for quote in quotes:
        contract = get_drift_contract_for_quote(quote.quote_id)
        if contract is None:
            continue
        existing = list_findings(quote.quote_id)
        if existing:
            continue
        try:
            run_drift_analysis(quote.quote_id, contract.contract_id)
        except Exception as exc:
            LOGGER.warning("Failed to analyze quote %s: %s", quote.quote_id, exc)

    return get_drift_dashboard()
