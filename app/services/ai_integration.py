from __future__ import annotations

import json
import logging
import re
from collections import OrderedDict
from copy import deepcopy
from datetime import date
from typing import Any

from app.config import get_ai_settings
from app.models import AIInvestigationBrief, AIStatus, Contract, ContractDocument, ExtractedObligation, InvoiceLine


LOGGER = logging.getLogger(__name__)
JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
CHAT_RESPONSE_CACHE_LIMIT = 64
CHAT_RESPONSE_CACHE: OrderedDict[tuple[str, str, str, str, str], dict[str, Any]] = OrderedDict()

_OPENAI_CLIENT: Any = None


def _get_cached_chat_response(cache_key: tuple[str, str, str, str, str]) -> dict[str, Any] | None:
    cached_response = CHAT_RESPONSE_CACHE.get(cache_key)
    if cached_response is None:
        return None

    CHAT_RESPONSE_CACHE.move_to_end(cache_key)
    return deepcopy(cached_response)


def _cache_chat_response(cache_key: tuple[str, str, str, str, str], payload: dict[str, Any]) -> None:
    CHAT_RESPONSE_CACHE[cache_key] = deepcopy(payload)
    CHAT_RESPONSE_CACHE.move_to_end(cache_key)
    while len(CHAT_RESPONSE_CACHE) > CHAT_RESPONSE_CACHE_LIMIT:
        CHAT_RESPONSE_CACHE.popitem(last=False)


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    items: list[str] = []
    for item in value:
        if item is None:
            continue
        text = item.strip() if isinstance(item, str) else str(item).strip()
        if text:
            items.append(text)
    return items


def _truncate_prompt_text(value: str, *, limit: int = 12000) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}\n...[truncated]"


def _should_use_low_priority_explanations() -> bool:
    settings = get_ai_settings()
    if not settings.enabled:
        return False

    return settings.provider != "github-models"


def get_ai_status() -> AIStatus:
    settings = get_ai_settings()
    if not settings.enabled:
        return AIStatus(
            enabled=False,
            provider=settings.provider,
            mode="rule-based-fallback",
            model=settings.model,
            extraction_strategy="regex fallback",
            explanation_strategy="template fallback",
        )

    return AIStatus(
        enabled=True,
        provider=settings.provider,
        mode="model-enhanced",
        model=settings.model,
        extraction_strategy="hosted chat-completions extraction and dossier resolution",
        explanation_strategy=(
            "hosted chat-completions explanation"
            if _should_use_low_priority_explanations()
            else "model-backed investigation brief with deterministic list copy"
        ),
    )


def _get_openai_client():
    global _OPENAI_CLIENT
    if _OPENAI_CLIENT is not None:
        return _OPENAI_CLIENT

    settings = get_ai_settings()

    from openai import OpenAI

    if settings.provider == "azure-foundry" and not settings.api_key:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://ai.azure.com/.default"
        )
        _OPENAI_CLIENT = OpenAI(
            base_url=settings.chat_completions_url,
            api_key=token_provider,
        )
    else:
        _OPENAI_CLIENT = OpenAI(
            base_url=settings.chat_completions_url,
            api_key=settings.api_key,
        )

    return _OPENAI_CLIENT


def _chat_completion_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    settings = get_ai_settings()
    if not settings.enabled:
        return None

    cache_key = (
        settings.provider,
        settings.chat_completions_url,
        settings.model or "",
        system_prompt,
        user_prompt,
    )
    cached_response = _get_cached_chat_response(cache_key)
    if cached_response is not None:
        return cached_response

    try:
        client = _get_openai_client()
        completion = client.chat.completions.create(
            model=settings.model or "gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            timeout=settings.timeout_seconds,
        )
    except Exception as exc:
        LOGGER.warning("AI request failed, falling back to deterministic logic: %s", exc)
        return None

    content = completion.choices[0].message.content if completion.choices else None
    if not isinstance(content, str):
        return None

    try:
        response_payload = json.loads(content)
    except json.JSONDecodeError:
        match = JSON_BLOCK_PATTERN.search(content)
        if match is None:
            LOGGER.warning("AI response did not contain valid JSON content")
            return None
        try:
            response_payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            LOGGER.warning("AI response JSON block was invalid")
            return None

    _cache_chat_response(cache_key, response_payload)
    return deepcopy(response_payload)


def try_extract_annual_uplift_from_text(
    *,
    contract_id: str,
    term_start: date,
    contract_text: str,
    document_id: str | None = None,
    page_number: int | None = None,
    extraction_method: str | None = None,
) -> ExtractedObligation | None:
    if not contract_text.strip():
        return None

    response = _chat_completion_json(
        system_prompt=(
            "You extract structured commercial obligations from contracts. "
            "Return strict JSON only. If no annual uplift clause exists, return {\"found\": false}."
        ),
        user_prompt=(
            "Extract annual uplift information from this contract or amendment text. "
            "Return JSON with keys: found, uplift_percent, notice_window_days, effective_date, source_clause_text, confidence_score. "
            "Only set found=true if the text contains a real commercial uplift obligation. "
            f"Contract start date: {term_start.isoformat()}. Contract text: {contract_text}"
        ),
    )
    if not response or not response.get("found"):
        return None

    try:
        uplift_percent = float(response["uplift_percent"])
        notice_window_days = int(response.get("notice_window_days") or 30)
        source_clause_text = str(response.get("source_clause_text") or contract_text)
        confidence_score = float(response.get("confidence_score") or 0.9)
    except (TypeError, ValueError, KeyError):
        LOGGER.warning("AI extraction payload was missing required uplift fields")
        return None

    effective_date = term_start.replace(year=term_start.year + 1)
    raw_effective_date = response.get("effective_date")
    if isinstance(raw_effective_date, str) and raw_effective_date.strip():
        try:
            effective_date = date.fromisoformat(raw_effective_date.strip())
        except ValueError:
            LOGGER.warning("AI extraction returned an invalid effective_date: %s", raw_effective_date)

    return ExtractedObligation(
        contract_id=contract_id,
        obligation_type="annual_uplift",
        value=uplift_percent,
        effective_date=effective_date,
        notice_window_days=notice_window_days,
        source_clause_text=source_clause_text,
        confidence_score=confidence_score,
        document_id=document_id,
        page_number=page_number,
        extraction_method=extraction_method,
    )


def try_extract_annual_uplift(contract: Contract) -> dict[str, Any] | None:
    obligation = try_extract_annual_uplift_from_text(
        contract_id=contract.contract_id,
        term_start=contract.term_start,
        contract_text=contract.raw_contract_text,
        extraction_method="ai-model",
    )
    if obligation is None:
        return None

    return {
        "value": obligation.value,
        "notice_window_days": obligation.notice_window_days,
        "source_clause_text": obligation.source_clause_text,
        "confidence_score": obligation.confidence_score,
    }


def resolve_annual_uplift_from_contract_dossier(
    *,
    contract: Contract,
    document_sources: list[dict[str, Any]],
    candidate_extractions: list[ExtractedObligation],
) -> ExtractedObligation | None:
    if not document_sources:
        return None

    response = _chat_completion_json(
        system_prompt=(
            "You resolve effective commercial uplift terms across a contract dossier. "
            "Use the contract record, amendments, renewal notices, and extracted candidates together. "
            "CRITICAL RULE: Document type hierarchy MUST be respected — amendments ALWAYS supersede the MSA and order forms, "
            "even if the amendment sets a LOWER rate than the MSA. An amendment that explicitly replaces or deletes a prior "
            "pricing clause is the controlling term regardless of whether the new rate is higher or lower. "
            "Later amendments or explicit overrides supersede earlier language. "
            "When a candidate extraction already exists, treat it as a strong hint from a previously extracted clause, not as noise. "
            "If a later amendment or later version supports that candidate, return found=true and select it. "
            "Only return found=false when the dossier genuinely contains no annual uplift obligation or every candidate is clearly contradicted by later controlling language. "
            "Return strict JSON only with keys found, uplift_percent, notice_window_days, effective_date, source_clause_text, confidence_score, source_document_id, page_number. "
            "Use source_document_id as null when the contract record text is the authoritative source."
        ),
        user_prompt=(
            "Resolve the currently effective annual uplift obligation for this contract dossier. "
            + json.dumps(
                {
                    "contract": {
                        "contract_id": contract.contract_id,
                        "account_id": contract.account_id,
                        "product_name": contract.product_name,
                        "term_start": contract.term_start.isoformat(),
                        "term_end": contract.term_end.isoformat(),
                        "base_price": contract.base_price,
                        "currency": contract.currency,
                        "quantity": contract.quantity,
                        "raw_contract_excerpt": _truncate_prompt_text(contract.raw_contract_text, limit=4000),
                    },
                    "candidate_extractions": [
                        {
                            "document_id": candidate.document_id,
                            "obligation_type": candidate.obligation_type,
                            "value": candidate.value,
                            "effective_date": candidate.effective_date.isoformat(),
                            "notice_window_days": candidate.notice_window_days,
                            "source_clause_text": candidate.source_clause_text,
                            "page_number": candidate.page_number,
                            "confidence_score": candidate.confidence_score,
                            "extraction_method": candidate.extraction_method,
                        }
                        for candidate in candidate_extractions
                    ],
                    "documents": [
                        {
                            "document_id": source.get("document_id"),
                            "document_type": source.get("document_type"),
                            "file_name": source.get("file_name"),
                            "version": source.get("version"),
                            "ingestion_status": source.get("ingestion_status"),
                            "page_count": source.get("page_count"),
                            "page_hint": source.get("page_hint"),
                            "excerpt": _truncate_prompt_text(str(source.get("excerpt") or ""), limit=4000),
                        }
                        for source in document_sources
                    ],
                },
                default=str,
            )
        ),
    )
    if not response or not response.get("found"):
        return None

    try:
        uplift_percent = float(response["uplift_percent"])
        notice_window_days = int(response.get("notice_window_days") or 30)
        source_clause_text = str(response.get("source_clause_text") or "").strip()
        confidence_score = float(response.get("confidence_score") or 0.9)
    except (TypeError, ValueError, KeyError):
        LOGGER.warning("AI dossier resolver payload was missing required uplift fields")
        return None

    if not source_clause_text:
        LOGGER.warning("AI dossier resolver returned an empty source clause")
        return None

    effective_date = contract.term_start.replace(year=contract.term_start.year + 1)
    raw_effective_date = response.get("effective_date")
    if isinstance(raw_effective_date, str) and raw_effective_date.strip():
        try:
            effective_date = date.fromisoformat(raw_effective_date.strip())
        except ValueError:
            LOGGER.warning("AI dossier resolver returned an invalid effective_date: %s", raw_effective_date)

    source_document_id: str | None = None
    raw_source_document_id = response.get("source_document_id")
    if isinstance(raw_source_document_id, str) and raw_source_document_id.strip():
        candidate_document_id = raw_source_document_id.strip()
        if candidate_document_id.lower() not in {"null", "none", "contract-record", "contract_record"}:
            source_document_id = candidate_document_id

    page_number: int | None = None
    raw_page_number = response.get("page_number")
    if raw_page_number not in (None, ""):
        try:
            page_number = int(raw_page_number)
        except (TypeError, ValueError):
            LOGGER.warning("AI dossier resolver returned an invalid page_number: %s", raw_page_number)

    return ExtractedObligation(
        contract_id=contract.contract_id,
        obligation_type="annual_uplift",
        value=uplift_percent,
        effective_date=effective_date,
        notice_window_days=notice_window_days,
        source_clause_text=source_clause_text,
        confidence_score=confidence_score,
        document_id=source_document_id,
        page_number=page_number,
        extraction_method="ai-resolved-commercial-terms",
    )


def explain_detected_case(
    *,
    contract: Contract,
    obligation: ExtractedObligation,
    actual_average: float,
    expected_amount: float,
    impact: float,
) -> dict[str, Any] | None:
    if not _should_use_low_priority_explanations():
        return None

    return _chat_completion_json(
        system_prompt=(
            "You explain contract revenue leakage findings for revenue operations teams. "
            "Return strict JSON with keys explanation and recommended_action."
        ),
        user_prompt=(
            "Summarize this missed uplift case in plain language. "
            f"Product: {contract.product_name}. Contract clause: {obligation.source_clause_text}. "
            f"Expected monthly amount: {expected_amount:.2f}. Actual average billed amount: {actual_average:.2f}. "
            f"Estimated missed revenue: {impact:.2f}."
        ),
    )


def explain_prediction(
    *,
    contract: Contract,
    obligation: ExtractedObligation,
    days_until_deadline: int,
    predicted_impact: float,
) -> dict[str, Any] | None:
    if not _should_use_low_priority_explanations():
        return None

    return _chat_completion_json(
        system_prompt=(
            "You generate preventive revenue-operations alerts. "
            "Return strict JSON with keys recommended_action and supporting_evidence."
        ),
        user_prompt=(
            "Create a preventive alert for an upcoming uplift deadline. "
            f"Product: {contract.product_name}. Clause: {obligation.source_clause_text}. "
            f"Days until notice deadline: {days_until_deadline}. Predicted impact: {predicted_impact:.2f}."
        ),
    )


def generate_investigation_brief(
    *,
    contract: Contract,
    obligation: ExtractedObligation | None,
    invoices: list[InvoiceLine],
    documents: list[ContractDocument],
    focus: str,
    metrics: dict[str, Any],
) -> AIInvestigationBrief | None:
    response = _chat_completion_json(
        system_prompt=(
            "You are an AI copilot for revenue operations investigations. "
            "Use only the provided contract, billing, and document facts. "
            "Return strict JSON with keys overview, root_cause, recommended_actions, evidence_points, document_notes."
        ),
        user_prompt=(
            "Create a concise investigation brief for this contract. "
            + json.dumps(
                {
                    "focus": focus,
                    "contract": {
                        "contract_id": contract.contract_id,
                        "account_id": contract.account_id,
                        "product_name": contract.product_name,
                        "term_start": contract.term_start.isoformat(),
                        "term_end": contract.term_end.isoformat(),
                        "base_price": contract.base_price,
                        "currency": contract.currency,
                        "quantity": contract.quantity,
                    },
                    "obligation": (
                        {
                            "obligation_type": obligation.obligation_type,
                            "value": obligation.value,
                            "effective_date": obligation.effective_date.isoformat(),
                            "notice_window_days": obligation.notice_window_days,
                            "source_clause_text": obligation.source_clause_text,
                            "confidence_score": obligation.confidence_score,
                            "document_id": obligation.document_id,
                            "extraction_method": obligation.extraction_method,
                        }
                        if obligation is not None
                        else None
                    ),
                    "metrics": metrics,
                    "documents": [
                        {
                            "document_type": document.document_type,
                            "file_name": document.file_name,
                            "version": document.version,
                            "ingestion_status": document.ingestion_status,
                        }
                        for document in documents
                    ],
                    "invoice_sample": [
                        {
                            "billing_period_start": invoice.billing_period_start.isoformat(),
                            "billing_period_end": invoice.billing_period_end.isoformat(),
                            "amount_billed": invoice.amount_billed,
                            "quantity": invoice.quantity,
                        }
                        for invoice in invoices[-6:]
                    ],
                },
                default=str,
            )
        ),
    )
    if not response:
        return None

    overview = response.get("overview")
    root_cause = response.get("root_cause")
    if not isinstance(overview, str) or not overview.strip() or not isinstance(root_cause, str) or not root_cause.strip():
        LOGGER.warning("AI investigation brief payload was missing required fields")
        return None

    return AIInvestigationBrief(
        focus=focus if focus in {"contract", "case", "prediction"} else "contract",
        generation_mode="model-generated",
        overview=overview.strip(),
        root_cause=root_cause.strip(),
        recommended_actions=_coerce_string_list(response.get("recommended_actions")),
        evidence_points=_coerce_string_list(response.get("evidence_points")),
        document_notes=_coerce_string_list(response.get("document_notes")),
    )
