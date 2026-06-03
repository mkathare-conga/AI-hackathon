"""
Amendment Impact Detector — service layer.

Analyzes amendments to identify downstream operational impacts:
billing changes needed, workflow updates, provisioning actions, and revenue effects.
"""
from __future__ import annotations

import json
import logging
import uuid

import psycopg
from psycopg.rows import dict_row

from app.config import get_ai_settings, get_data_settings
from app.models_amendment import (
    AmendmentActionItem,
    AmendmentAnalysis,
    AmendmentAnalysisDetail,
    AmendmentDashboard,
    AmendmentImpact,
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

def list_analyses() -> list[AmendmentAnalysis]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM amendment_analyses ORDER BY amendment_date DESC")
            return [AmendmentAnalysis(**row) for row in cur.fetchall()]


def get_analysis(analysis_id: str) -> AmendmentAnalysis | None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM amendment_analyses WHERE analysis_id = %s", (analysis_id,))
            row = cur.fetchone()
            return AmendmentAnalysis(**row) if row else None


def get_analysis_detail(analysis_id: str) -> AmendmentAnalysisDetail | None:
    analysis = get_analysis(analysis_id)
    if analysis is None:
        return None

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM amendment_impacts WHERE analysis_id = %s ORDER BY severity, impact_id", (analysis_id,))
            impacts = [AmendmentImpact(**row) for row in cur.fetchall()]
            cur.execute("SELECT * FROM amendment_action_items WHERE analysis_id = %s ORDER BY priority, action_id", (analysis_id,))
            actions = [AmendmentActionItem(**row) for row in cur.fetchall()]

    return AmendmentAnalysisDetail(analysis=analysis, impacts=impacts, action_items=actions)


def list_impacts(analysis_id: str) -> list[AmendmentImpact]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM amendment_impacts WHERE analysis_id = %s ORDER BY severity, impact_id", (analysis_id,))
            return [AmendmentImpact(**row) for row in cur.fetchall()]


def list_action_items(analysis_id: str | None = None, status: str | None = None) -> list[AmendmentActionItem]:
    with _conn() as conn:
        with conn.cursor() as cur:
            query = "SELECT * FROM amendment_action_items WHERE 1=1"
            params: list = []
            if analysis_id:
                query += " AND analysis_id = %s"
                params.append(analysis_id)
            if status:
                query += " AND status = %s"
                params.append(status)
            query += " ORDER BY priority, action_id"
            cur.execute(query, params)
            return [AmendmentActionItem(**row) for row in cur.fetchall()]


def update_action_status(action_id: str, new_status: str) -> AmendmentActionItem | None:
    valid_statuses = ("open", "in_progress", "completed", "dismissed")
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}")
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE amendment_action_items SET status = %s WHERE action_id = %s RETURNING *",
                (new_status, action_id),
            )
            conn.commit()
            row = cur.fetchone()
            return AmendmentActionItem(**row) if row else None


# ─── Dashboard ────────────────────────────────────────────────────────────────

def get_amendment_dashboard() -> AmendmentDashboard:
    analyses = list_analyses()
    all_details: list[AmendmentAnalysisDetail] = []

    for analysis in analyses:
        detail = get_analysis_detail(analysis.analysis_id)
        if detail:
            all_details.append(detail)

    total_impacts = sum(len(d.impacts) for d in all_details)
    open_actions = sum(
        1 for d in all_details
        for a in d.action_items
        if a.status in ("open", "in_progress")
    )
    net_delta = sum(a.analysis.total_annual_revenue_delta for a in all_details)
    positive = sum(1 for a in all_details if a.analysis.total_annual_revenue_delta > 0)
    negative = sum(1 for a in all_details if a.analysis.total_annual_revenue_delta < 0)

    return AmendmentDashboard(
        total_analyses=len(all_details),
        total_impacts=total_impacts,
        total_action_items_open=open_actions,
        net_annual_revenue_delta=round(net_delta, 2),
        positive_amendments=positive,
        negative_amendments=negative,
        analyses=all_details,
    )


# ─── AI-powered amendment analysis ───────────────────────────────────────────

def _chat_completion_json(system_prompt: str, user_prompt: str) -> dict | None:
    """Call the AI backend for amendment analysis."""
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
        LOGGER.warning("AI request failed for amendment analysis: %s", exc)
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


def analyze_amendment_text(
    contract_id: str,
    account_name: str,
    original_contract_text: str,
    amendment_text: str,
    amendment_date: str,
) -> AmendmentAnalysisDetail:
    """Analyze an amendment against its original contract and produce impact findings + action items."""

    analysis_id = f"amend-analysis-{_short_id()}"

    # Try AI analysis first
    ai_result = _analyze_with_ai(original_contract_text, amendment_text)

    if ai_result is None:
        # Deterministic fallback
        ai_result = _analyze_deterministic(original_contract_text, amendment_text)

    # Build analysis record
    impacts: list[AmendmentImpact] = []
    action_items: list[AmendmentActionItem] = []

    for impact_data in ai_result.get("impacts", []):
        impact_id = f"impact-{_short_id()}"
        impact = AmendmentImpact(
            impact_id=impact_id,
            analysis_id=analysis_id,
            contract_id=contract_id,
            impact_category=_validate_category(impact_data.get("category", "pricing_change")),
            before_value=str(impact_data.get("before", "Unknown")),
            after_value=str(impact_data.get("after", "Unknown")),
            severity=_validate_severity(impact_data.get("severity", "medium")),
            annual_revenue_delta=_safe_float(impact_data.get("annual_revenue_delta")),
            requires_billing_update=bool(impact_data.get("requires_billing_update", False)),
            requires_workflow_update=bool(impact_data.get("requires_workflow_update", False)),
            explanation=str(impact_data.get("explanation", "Change detected.")),
            source_clause_text=impact_data.get("source_clause_text"),
            confidence_score=float(impact_data.get("confidence_score", 0.85)),
        )
        impacts.append(impact)

        # Generate action items for this impact
        for action_data in impact_data.get("actions", []):
            action_items.append(AmendmentActionItem(
                action_id=f"action-{_short_id()}",
                analysis_id=analysis_id,
                impact_id=impact_id,
                action_type=_validate_action_type(action_data.get("type", "update_billing")),
                description=str(action_data.get("description", "Review change.")),
                priority=_validate_priority(action_data.get("priority", "medium")),
                status="open",
                assigned_team=action_data.get("team"),
            ))

    high_count = sum(1 for i in impacts if i.severity == "high")
    total_delta = sum(i.annual_revenue_delta or 0 for i in impacts)

    analysis = AmendmentAnalysis(
        analysis_id=analysis_id,
        contract_id=contract_id,
        account_name=account_name,
        amendment_summary=ai_result.get("summary", "Amendment analyzed."),
        amendment_date=amendment_date,
        total_changes=len(impacts),
        high_impact_count=high_count,
        total_annual_revenue_delta=round(total_delta, 2),
        status="analyzed",
    )

    # Persist
    _persist_analysis(analysis, impacts, action_items)

    return AmendmentAnalysisDetail(analysis=analysis, impacts=impacts, action_items=action_items)


def _analyze_with_ai(original_text: str, amendment_text: str) -> dict | None:
    return _chat_completion_json(
        system_prompt=(
            "You analyze contract amendments to identify operational impacts. "
            "Compare the amendment against the original contract and identify all changes. "
            "For each change, determine: category, before value, after value, severity, "
            "annual revenue impact, whether billing needs updating, whether workflows need updating, "
            "and what action items are needed. "
            "Return strict JSON with keys: summary (one sentence), impacts (array of objects). "
            "Each impact has: category (one of: pricing_change, quantity_change, term_extension, "
            "term_reduction, support_change, scope_addition, scope_removal, renewal_terms_change, "
            "payment_terms_change, liability_change, sla_change), before, after, severity (high/medium/low), "
            "annual_revenue_delta (number, negative if revenue decreasing), requires_billing_update (bool), "
            "requires_workflow_update (bool), explanation, source_clause_text, confidence_score, "
            "actions (array with type, description, priority, team)."
        ),
        user_prompt=(
            "Analyze this amendment and identify all downstream impacts.\n\n"
            f"ORIGINAL CONTRACT:\n{original_text[:6000]}\n\n"
            f"AMENDMENT:\n{amendment_text[:6000]}"
        ),
    )


def _analyze_deterministic(original_text: str, amendment_text: str) -> dict:
    """Regex/heuristic fallback for amendment analysis."""
    import re

    impacts = []
    text_lower = amendment_text.lower()

    # Check for uplift changes
    uplift_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:annual|yearly)?\s*(?:uplift|increase|escalation)", amendment_text, re.IGNORECASE)
    if uplift_match:
        new_rate = float(uplift_match.group(1))
        old_match = re.search(r"(?:prior|previous|original|was|from)\s*(?:rate\s*(?:of\s*)?)(\d+(?:\.\d+)?)\s*%", amendment_text, re.IGNORECASE)
        old_rate = float(old_match.group(1)) if old_match else 0
        impacts.append({
            "category": "renewal_terms_change",
            "before": f"{old_rate}% annual uplift" if old_rate else "Previous rate",
            "after": f"{new_rate}% annual uplift",
            "severity": "high",
            "annual_revenue_delta": 0,
            "requires_billing_update": True,
            "requires_workflow_update": True,
            "explanation": f"Annual uplift rate changed to {new_rate}%. Billing and renewal workflows need updating.",
            "source_clause_text": uplift_match.group(0),
            "confidence_score": 0.8,
            "actions": [
                {"type": "update_billing", "description": f"Update billing uplift rate to {new_rate}%.", "priority": "urgent", "team": "Revenue Operations"},
                {"type": "update_renewal_workflow", "description": "Update renewal workflow with new rate.", "priority": "high", "team": "Revenue Operations"},
            ],
        })

    # Check for term changes
    if "extend" in text_lower or "co-terminat" in text_lower:
        impacts.append({
            "category": "term_extension",
            "before": "Original term",
            "after": "Extended term",
            "severity": "medium",
            "annual_revenue_delta": 0,
            "requires_billing_update": False,
            "requires_workflow_update": True,
            "explanation": "Subscription term has been extended. Renewal dates and workflows need updating.",
            "source_clause_text": None,
            "confidence_score": 0.7,
            "actions": [
                {"type": "update_renewal_workflow", "description": "Update contract end date in CRM.", "priority": "medium", "team": "Sales Operations"},
            ],
        })

    # Check for payment terms
    payment_match = re.search(r"net\s+(\d+)\s*days?", amendment_text, re.IGNORECASE)
    if payment_match:
        new_days = int(payment_match.group(1))
        if new_days > 30:
            impacts.append({
                "category": "payment_terms_change",
                "before": "Net 30 days",
                "after": f"Net {new_days} days",
                "severity": "low",
                "annual_revenue_delta": 0,
                "requires_billing_update": True,
                "requires_workflow_update": False,
                "explanation": f"Payment terms changed to net {new_days} days. Update invoicing configuration.",
                "source_clause_text": payment_match.group(0),
                "confidence_score": 0.75,
                "actions": [
                    {"type": "update_billing", "description": f"Change payment terms to net {new_days}.", "priority": "medium", "team": "Finance"},
                ],
            })

    return {
        "summary": f"Amendment contains {len(impacts)} identifiable change(s).",
        "impacts": impacts,
    }


# ─── Validation helpers ───────────────────────────────────────────────────────

_VALID_CATEGORIES = {
    "pricing_change", "quantity_change", "term_extension", "term_reduction",
    "support_change", "scope_addition", "scope_removal", "renewal_terms_change",
    "payment_terms_change", "liability_change", "sla_change",
}

_VALID_ACTION_TYPES = {
    "update_billing", "update_renewal_workflow", "notify_customer",
    "update_support_tier", "review_sla", "update_provisioning", "legal_review",
}


def _validate_category(value: str) -> str:
    return value if value in _VALID_CATEGORIES else "pricing_change"


def _validate_severity(value: str) -> str:
    return value if value in ("high", "medium", "low") else "medium"


def _validate_priority(value: str) -> str:
    return value if value in ("urgent", "high", "medium", "low") else "medium"


def _validate_action_type(value: str) -> str:
    return value if value in _VALID_ACTION_TYPES else "update_billing"


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ─── Persistence ──────────────────────────────────────────────────────────────

def _persist_analysis(
    analysis: AmendmentAnalysis,
    impacts: list[AmendmentImpact],
    actions: list[AmendmentActionItem],
) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO amendment_analyses
                    (analysis_id, contract_id, account_name, amendment_summary,
                     amendment_date, total_changes, high_impact_count,
                     total_annual_revenue_delta, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (analysis_id) DO NOTHING""",
                (analysis.analysis_id, analysis.contract_id, analysis.account_name,
                 analysis.amendment_summary, analysis.amendment_date,
                 analysis.total_changes, analysis.high_impact_count,
                 analysis.total_annual_revenue_delta, analysis.status),
            )
            for i in impacts:
                cur.execute(
                    """INSERT INTO amendment_impacts
                        (impact_id, analysis_id, contract_id, impact_category,
                         before_value, after_value, severity, annual_revenue_delta,
                         requires_billing_update, requires_workflow_update,
                         explanation, source_clause_text, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (impact_id) DO NOTHING""",
                    (i.impact_id, i.analysis_id, i.contract_id, i.impact_category,
                     i.before_value, i.after_value, i.severity, i.annual_revenue_delta,
                     i.requires_billing_update, i.requires_workflow_update,
                     i.explanation, i.source_clause_text, i.confidence_score),
                )
            for a in actions:
                cur.execute(
                    """INSERT INTO amendment_action_items
                        (action_id, analysis_id, impact_id, action_type,
                         description, priority, status, assigned_team)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (action_id) DO NOTHING""",
                    (a.action_id, a.analysis_id, a.impact_id, a.action_type,
                     a.description, a.priority, a.status, a.assigned_team),
                )
            conn.commit()
