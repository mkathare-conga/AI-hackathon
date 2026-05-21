from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache

from app.data_loader import (
    load_accounts,
    load_contract_documents,
    load_contracts,
    load_invoice_lines,
    load_obligation_extractions,
    load_renewal_events,
)
from app.services.ai_integration import (
    explain_detected_case,
    explain_prediction,
    resolve_annual_uplift_from_contract_dossier,
    try_extract_annual_uplift,
)
from app.models import (
    AIInvestigationBrief,
    Contract,
    ContractFactsResponse,
    DashboardSummary,
    ExtractedObligation,
    InvoiceLine,
    LeakageCase,
    RiskPrediction,
)
from app.services.document_text import extract_document_text
from app.services.documents import get_contract_document_bytes
from app.services.ai_integration import generate_investigation_brief


UPLIFT_PATTERN = re.compile(r"(?P<percent>\d+(?:\.\d+)?)%\s+(?:annual\s+)?(?:price\s+)?(?:increase|uplift)", re.IGNORECASE)
NOTICE_PATTERN = re.compile(r"(?P<days>\d+)\s+days?\s+notice", re.IGNORECASE)
PARAGRAPH_BREAK_PATTERN = re.compile(r"(?:\r?\n){2,}")
COMMERCIAL_TERM_PATTERN = re.compile(
    r"(increase|uplift|pricing|renewal|notice|supersed|override|replace|amend)",
    re.IGNORECASE,
)
PRECEDENCE_HINT_PATTERN = re.compile(
    r"(supersed|override|replace|control(?:s|ling)?|later amendment|latest amendment|most recent)",
    re.IGNORECASE,
)
DOCUMENT_PRECEDENCE = {
    "amendment": 4,
    "renewal_notice": 3,
    "order_form": 2,
    "msa": 1,
    "nda": 0,
}


def _extract_clause_excerpt(contract_text: str, match_start: int) -> str:
    paragraph_breaks = list(PARAGRAPH_BREAK_PATTERN.finditer(contract_text))
    preceding_break = next((match for match in reversed(paragraph_breaks) if match.end() <= match_start), None)
    following_break = next((match for match in paragraph_breaks if match.start() >= match_start), None)

    start_index = 0 if preceding_break is None else preceding_break.end()
    end_index = len(contract_text) if following_break is None else following_break.start()
    excerpt = contract_text[start_index:end_index].strip()
    if excerpt:
        return excerpt

    sentence_start = max(contract_text.rfind(". ", 0, match_start), contract_text.rfind("\n", 0, match_start))
    sentence_end = contract_text.find(".", match_start)
    start_index = 0 if sentence_start == -1 else sentence_start + 2
    end_index = len(contract_text) if sentence_end == -1 else sentence_end + 1
    return contract_text[start_index:end_index].strip()


def _extract_relevant_excerpt(contract_text: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in PARAGRAPH_BREAK_PATTERN.split(contract_text) if paragraph.strip()]
    relevant_paragraphs = [paragraph for paragraph in paragraphs if COMMERCIAL_TERM_PATTERN.search(paragraph)]
    if relevant_paragraphs:
        return "\n\n".join(relevant_paragraphs[:4])

    return contract_text[:4000].strip()


def _has_relevant_commercial_terms(contract_text: str) -> bool:
    return bool(COMMERCIAL_TERM_PATTERN.search(contract_text))


def extract_annual_uplift_from_text(
    *,
    contract_id: str,
    term_start: date,
    contract_text: str,
    confidence_score: float = 0.97,
    document_id: str | None = None,
    page_number: int | None = None,
    extraction_method: str | None = None,
) -> list[ExtractedObligation]:
    uplift_match = UPLIFT_PATTERN.search(contract_text)
    if uplift_match is None:
        return []

    notice_match = NOTICE_PATTERN.search(contract_text)
    uplift_percent = float(uplift_match.group("percent"))
    notice_days = int(notice_match.group("days")) if notice_match else 30
    effective_date = term_start.replace(year=term_start.year + 1)
    clause_excerpt = _extract_clause_excerpt(contract_text, uplift_match.start())

    return [
        ExtractedObligation(
            contract_id=contract_id,
            obligation_type="annual_uplift",
            value=uplift_percent,
            effective_date=effective_date,
            notice_window_days=notice_days,
            source_clause_text=clause_excerpt,
            confidence_score=confidence_score,
            document_id=document_id,
            page_number=page_number,
            extraction_method=extraction_method,
        )
    ]


def _extract_annual_uplift_with_regex(contract: Contract) -> list[ExtractedObligation]:
    return extract_annual_uplift_from_text(
        contract_id=contract.contract_id,
        term_start=contract.term_start,
        contract_text=contract.raw_contract_text,
        confidence_score=0.97,
        extraction_method="regex-contract-text",
    )


def _load_persisted_annual_uplift(contract_id: str) -> list[ExtractedObligation]:
    persisted_rows = load_obligation_extractions(contract_id=contract_id)
    return [
        ExtractedObligation(
            contract_id=row.contract_id,
            obligation_type=row.obligation_type,
            value=row.value,
            effective_date=row.effective_date,
            notice_window_days=row.notice_window_days,
            source_clause_text=row.source_clause_text,
            confidence_score=row.confidence_score,
            document_id=row.document_id,
            page_number=row.page_number,
            extraction_method=row.extraction_method,
        )
        for row in persisted_rows
        if row.obligation_type == "annual_uplift"
    ]


def _same_obligation(left: ExtractedObligation, right: ExtractedObligation) -> bool:
    return (
        left.document_id == right.document_id
        and left.value == right.value
        and left.notice_window_days == right.notice_window_days
        and left.effective_date == right.effective_date
        and left.source_clause_text == right.source_clause_text
    )


def _same_obligation_terms(left: ExtractedObligation | None, right: ExtractedObligation | None) -> bool:
    if left is None or right is None:
        return False

    return (
        left.value == right.value
        and left.notice_window_days == right.notice_window_days
        and left.effective_date == right.effective_date
    )


def _document_precedence_rank(document_type: str | None) -> int:
    if not document_type:
        return -1
    return DOCUMENT_PRECEDENCE.get(document_type, -1)


def _candidate_resolution_score(
    candidate: ExtractedObligation,
    document: ContractDocument | None,
) -> tuple[int, int, int, int, float]:
    return (
        1 if PRECEDENCE_HINT_PATTERN.search(candidate.source_clause_text) else 0,
        _document_precedence_rank(document.document_type if document else None),
        document.version if document else 0,
        candidate.effective_date.toordinal(),
        candidate.confidence_score,
    )


def _resolve_annual_uplift_with_rules(
    contract: Contract,
    persisted_extractions: list[ExtractedObligation],
) -> ExtractedObligation | None:
    if not persisted_extractions:
        return None

    documents_by_id = {
        document.document_id: document for document in load_contract_documents(contract.contract_id)
    }
    selected = max(
        persisted_extractions,
        key=lambda candidate: _candidate_resolution_score(candidate, documents_by_id.get(candidate.document_id)),
    ).model_copy(deep=True)
    selected.extraction_method = "rule-resolved-commercial-terms"
    return selected


def _build_candidate_annual_uplift_evidence(
    contract_id: str,
    resolved_obligation: ExtractedObligation | None,
) -> list[ExtractedObligation]:
    candidates = _load_persisted_annual_uplift(contract_id)
    if resolved_obligation is None:
        return candidates

    if any(_same_obligation(candidate, resolved_obligation) for candidate in candidates):
        return candidates

    return [resolved_obligation, *candidates]


@lru_cache(maxsize=128)
def _load_document_text_payload(document_id: str) -> tuple[str, int | None, int | None, str] | None:
    # Fast path: read pre-extracted text from DB (persisted at ingestion time)
    from app.postgres_loader import load_document_extracted_text

    db_result = load_document_extracted_text(document_id)
    if db_result is not None:
        text, _excerpt, page_count = db_result
        return (text, page_count, None, "db-persisted-text")

    # Fallback: fetch from MinIO for legacy documents without persisted text
    try:
        result = get_contract_document_bytes(document_id)
    except Exception:
        return None
    if result is None:
        return None

    document, payload = result
    return extract_document_text(document.mime_type, payload, page_hint_pattern=UPLIFT_PATTERN)


def _resolve_dossier_annual_uplift(
    contract: Contract,
    persisted_extractions: list[ExtractedObligation],
) -> ExtractedObligation | None:
    documents = load_contract_documents(contract.contract_id)
    if not documents:
        return None

    candidate_document_ids = {candidate.document_id for candidate in persisted_extractions if candidate.document_id}
    document_sources: list[dict[str, object]] = []
    for document in documents:
        extracted_payload = _load_document_text_payload(document.document_id)
        if extracted_payload is None:
            continue

        text, page_count, page_hint, _ = extracted_payload
        if not text.strip():
            continue
        if document.document_id not in candidate_document_ids and not _has_relevant_commercial_terms(text):
            continue

        document_sources.append(
            {
                "document_id": document.document_id,
                "document_type": document.document_type,
                "file_name": document.file_name,
                "version": document.version,
                "ingestion_status": document.ingestion_status,
                "page_count": page_count or document.page_count,
                "page_hint": page_hint,
                "excerpt": _extract_relevant_excerpt(text),
            }
        )

    if not document_sources:
        return None

    ai_resolved = resolve_annual_uplift_from_contract_dossier(
        contract=contract,
        document_sources=document_sources,
        candidate_extractions=persisted_extractions,
    )
    if ai_resolved is not None:
        return ai_resolved

    return _resolve_annual_uplift_with_rules(contract, persisted_extractions)


@lru_cache(maxsize=128)
def _get_governing_annual_uplift_cached(contract_id: str) -> ExtractedObligation | None:
    contracts = {contract.contract_id: contract for contract in load_contracts()}
    contract = contracts.get(contract_id)
    if contract is None:
        return None

    return _compute_governing_annual_uplift(contract)


def _compute_governing_annual_uplift(contract: Contract) -> ExtractedObligation | None:
    persisted_extractions = _load_persisted_annual_uplift(contract.contract_id)
    resolved_extraction = _resolve_dossier_annual_uplift(contract, persisted_extractions)
    if resolved_extraction is not None:
        return resolved_extraction.model_copy(deep=True)

    if persisted_extractions:
        rule_resolved = _resolve_annual_uplift_with_rules(contract, persisted_extractions)
        if rule_resolved is not None:
            return rule_resolved.model_copy(deep=True)

    ai_extraction = try_extract_annual_uplift(contract)
    if ai_extraction is not None:
        return ExtractedObligation(
            contract_id=contract.contract_id,
            obligation_type="annual_uplift",
            value=float(ai_extraction["value"]),
            effective_date=contract.term_start.replace(year=contract.term_start.year + 1),
            notice_window_days=int(ai_extraction["notice_window_days"]),
            source_clause_text=str(ai_extraction["source_clause_text"]),
            confidence_score=float(ai_extraction["confidence_score"]),
            extraction_method="ai-model",
        )

    regex_extractions = _extract_annual_uplift_with_regex(contract)
    return regex_extractions[0].model_copy(deep=True) if regex_extractions else None


def get_governing_annual_uplift(contract_id: str) -> ExtractedObligation | None:
    obligation = _get_governing_annual_uplift_cached(contract_id)
    return obligation.model_copy(deep=True) if obligation is not None else None


def clear_leakage_resolution_caches() -> None:
    _get_governing_annual_uplift_cached.cache_clear()
    _load_document_text_payload.cache_clear()


def _extract_annual_uplift(contract: Contract, *, prefer_dossier_resolution: bool = False) -> list[ExtractedObligation]:
    if prefer_dossier_resolution:
        resolved_extraction = _compute_governing_annual_uplift(contract)
        if resolved_extraction is not None:
            return [resolved_extraction]

    persisted_extractions = _load_persisted_annual_uplift(contract.contract_id)

    if persisted_extractions:
        return persisted_extractions

    ai_extraction = try_extract_annual_uplift(contract)
    if ai_extraction is not None:
        return [
            ExtractedObligation(
                contract_id=contract.contract_id,
                obligation_type="annual_uplift",
                value=float(ai_extraction["value"]),
                effective_date=contract.term_start.replace(year=contract.term_start.year + 1),
                notice_window_days=int(ai_extraction["notice_window_days"]),
                source_clause_text=str(ai_extraction["source_clause_text"]),
                confidence_score=float(ai_extraction["confidence_score"]),
                extraction_method="ai-model",
            )
        ]

    return _extract_annual_uplift_with_regex(contract)


def _default_case_explanation(
    *,
    obligation: ExtractedObligation,
    actual_average: float,
    expected_amount: float,
) -> str:
    return (
        f"The contract allows a {obligation.value:.0f}% annual uplift effective {obligation.effective_date.isoformat()}, "
        f"but invoices are still averaging {actual_average:.2f} instead of {expected_amount:.2f}."
    )


def _default_case_action() -> str:
    return "Review billing configuration and issue the uplift notice or billing correction."


def _describe_documents(contract_id: str) -> list[str]:
    documents = load_contract_documents(contract_id)
    if not documents:
        return ["No uploaded contract documents are attached; analysis is based on the contract record text."]

    return [
        f"{document.file_name} ({document.document_type.replace('_', ' ')}, {document.ingestion_status}, v{document.version})"
        for document in documents
    ]


def _build_brief_metrics(
    *,
    contract: Contract,
    obligation: ExtractedObligation | None,
    invoices: list[InvoiceLine],
    focus: str,
    today: date,
) -> dict[str, object]:
    metrics: dict[str, object] = {
        "invoice_count": len(invoices),
        "latest_invoice_amount": invoices[-1].amount_billed if invoices else None,
    }
    if obligation is None:
        return metrics

    if focus == "case":
        after_effective_invoices = [
            invoice
            for invoice in invoices
            if invoice.billing_period_start >= obligation.effective_date and invoice.billing_period_start <= today
        ]
        expected_amount = round(contract.base_price * (1 + (obligation.value / 100)) * contract.quantity, 2)
        actual_average = round(
            sum(invoice.amount_billed for invoice in after_effective_invoices) / len(after_effective_invoices),
            2,
        ) if after_effective_invoices else None
        estimated_impact = round(
            sum(max(expected_amount - invoice.amount_billed, 0) for invoice in after_effective_invoices),
            2,
        ) if after_effective_invoices else 0.0
        metrics.update(
            {
                "expected_amount": expected_amount,
                "actual_average": actual_average,
                "estimated_impact": estimated_impact,
                "effective_invoice_count": len(after_effective_invoices),
            }
        )
        return metrics

    notice_deadline = obligation.effective_date - timedelta(days=obligation.notice_window_days)
    metrics.update(
        {
            "notice_deadline": notice_deadline.isoformat(),
            "days_until_deadline": (notice_deadline - today).days,
            "predicted_impact": round(contract.base_price * contract.quantity * (obligation.value / 100), 2),
        }
    )
    return metrics


def get_contract_ai_brief(
    contract_id: str,
    *,
    focus: str = "contract",
    today: date | None = None,
) -> AIInvestigationBrief | None:
    facts = get_contract_facts(contract_id)
    if facts is None:
        return None

    normalized_focus = focus if focus in {"contract", "case", "prediction"} else "contract"
    as_of = today or date.today()
    obligation = facts.obligations[0] if facts.obligations else None
    metrics = _build_brief_metrics(
        contract=facts.contract,
        obligation=obligation,
        invoices=facts.invoices,
        focus=normalized_focus,
        today=as_of,
    )
    ai_brief = generate_investigation_brief(
        contract=facts.contract,
        obligation=obligation,
        invoices=facts.invoices,
        documents=facts.documents,
        focus=normalized_focus,
        metrics=metrics,
    )
    if ai_brief is not None:
        return ai_brief

    if obligation is None:
        return AIInvestigationBrief(
            focus=normalized_focus,
            generation_mode="template-fallback",
            overview="No uplift obligation has been extracted yet, so the contract needs document review before leakage can be quantified.",
            root_cause="The current dossier does not contain a structured annual uplift finding.",
            recommended_actions=[
                "Upload the latest amendment, order form, or renewal notice.",
                "Re-run document parsing to capture any commercial uplift terms.",
            ],
            evidence_points=["No annual uplift obligation is currently available in contract facts."],
            document_notes=_describe_documents(contract_id),
        )

    if normalized_focus == "prediction":
        days_until_deadline = metrics.get("days_until_deadline")
        predicted_impact = metrics.get("predicted_impact")
        return AIInvestigationBrief(
            focus=normalized_focus,
            generation_mode="template-fallback",
            overview=(
                f"This contract has a {obligation.value:.0f}% uplift clause and the next notice deadline is approaching, "
                f"putting about {predicted_impact:.2f} at risk if notice is missed."
            ),
            root_cause=(
                f"The contract requires {obligation.notice_window_days} days notice before the {obligation.effective_date.isoformat()} "
                f"renewal uplift takes effect, leaving {days_until_deadline} days to act."
            ),
            recommended_actions=[
                f"Send the renewal uplift notice within {days_until_deadline} days.",
                "Confirm the renewal workflow has a recorded notice_sent event.",
            ],
            evidence_points=[
                f"Clause evidence: {obligation.source_clause_text}",
                f"Predicted renewal impact: {predicted_impact:.2f}.",
            ],
            document_notes=_describe_documents(contract_id),
        )

    expected_amount = metrics.get("expected_amount")
    actual_average = metrics.get("actual_average")
    estimated_impact = metrics.get("estimated_impact")
    return AIInvestigationBrief(
        focus=normalized_focus,
        generation_mode="template-fallback",
        overview=(
            f"This contract appears to be underbilling against a {obligation.value:.0f}% contractual uplift, "
            f"with about {estimated_impact:.2f} of missed revenue detected so far."
        ),
        root_cause=(
            f"Invoices after {obligation.effective_date.isoformat()} are averaging {actual_average:.2f} while the expected uplifted amount is {expected_amount:.2f}."
        ),
        recommended_actions=[
            _default_case_action(),
            "Validate that the billing system references the latest uploaded amendment or renewal terms.",
        ],
        evidence_points=[
            f"Clause evidence: {obligation.source_clause_text}",
            f"Expected billed amount: {expected_amount:.2f}; actual average billed amount: {actual_average:.2f}.",
        ],
        document_notes=_describe_documents(contract_id),
    )


def _group_invoices() -> dict[str, list[InvoiceLine]]:
    grouped: dict[str, list[InvoiceLine]] = defaultdict(list)
    for invoice in load_invoice_lines():
        grouped[invoice.contract_id].append(invoice)
    return grouped


def get_contract_facts(contract_id: str) -> ContractFactsResponse | None:
    contracts = {contract.contract_id: contract for contract in load_contracts()}
    contract = contracts.get(contract_id)
    if contract is None:
        return None

    invoices = sorted(_group_invoices().get(contract_id, []), key=lambda item: item.billing_period_start)
    events = [event for event in load_renewal_events() if event.contract_id == contract_id]
    obligations = _extract_annual_uplift(contract, prefer_dossier_resolution=True)
    selected_obligation = obligations[0] if obligations else None

    return ContractFactsResponse(
        contract=contract,
        obligations=obligations,
        candidate_obligations=_build_candidate_annual_uplift_evidence(contract_id, selected_obligation),
        invoices=invoices,
        renewal_events=events,
        documents=load_contract_documents(contract_id),
    )


def get_leakage_cases(today: date | None = None) -> list[LeakageCase]:
    as_of = today or date.today()
    accounts = {account.account_id: account for account in load_accounts()}
    invoices_by_contract = _group_invoices()
    cases: list[LeakageCase] = []

    for contract in load_contracts():
        obligation = get_governing_annual_uplift(contract.contract_id)
        if obligation is None:
            continue
        after_effective_invoices = [
            invoice
            for invoice in invoices_by_contract.get(contract.contract_id, [])
            if invoice.billing_period_start >= obligation.effective_date and invoice.billing_period_start <= as_of
        ]
        if not after_effective_invoices:
            continue

        expected_amount = round(contract.base_price * (1 + (obligation.value / 100)) * contract.quantity, 2)
        actual_average = round(
            sum(invoice.amount_billed for invoice in after_effective_invoices) / len(after_effective_invoices),
            2,
        )

        if actual_average >= expected_amount:
            continue

        impact = round(sum(max(expected_amount - invoice.amount_billed, 0) for invoice in after_effective_invoices), 2)
        account = accounts[contract.account_id]
        ai_explanation = explain_detected_case(
            contract=contract,
            obligation=obligation,
            actual_average=actual_average,
            expected_amount=expected_amount,
            impact=impact,
        )
        cases.append(
            LeakageCase(
                case_id=f"case-{contract.contract_id}",
                contract_id=contract.contract_id,
                account_id=contract.account_id,
                account_name=account.name,
                case_type="missed_uplift",
                expected_value=expected_amount,
                actual_value=actual_average,
                estimated_impact=impact,
                confidence_score=0.95,
                explanation=str(
                    ai_explanation.get("explanation")
                    if ai_explanation and ai_explanation.get("explanation")
                    else _default_case_explanation(
                        obligation=obligation,
                        actual_average=actual_average,
                        expected_amount=expected_amount,
                    )
                ),
                recommended_action=str(
                    ai_explanation.get("recommended_action")
                    if ai_explanation and ai_explanation.get("recommended_action")
                    else _default_case_action()
                ),
            )
        )

    return sorted(cases, key=lambda item: item.estimated_impact, reverse=True)


def get_leakage_case(case_id: str, today: date | None = None) -> LeakageCase | None:
    for item in get_leakage_cases(today=today):
        if item.case_id == case_id:
            return item
    return None


def get_risk_predictions(today: date | None = None) -> list[RiskPrediction]:
    as_of = today or date.today()
    accounts = {account.account_id: account for account in load_accounts()}
    events_by_contract: dict[str, list[str]] = defaultdict(list)
    for event in load_renewal_events():
        events_by_contract[event.contract_id].append(event.event_type)

    predictions: list[RiskPrediction] = []
    for contract in load_contracts():
        obligation = get_governing_annual_uplift(contract.contract_id)
        if obligation is None:
            continue
        notice_deadline = obligation.effective_date - timedelta(days=obligation.notice_window_days)
        days_until_deadline = (notice_deadline - as_of).days
        if not (0 <= days_until_deadline <= 45):
            continue

        existing_events = events_by_contract.get(contract.contract_id, [])
        if "notice_sent" in existing_events:
            continue

        predicted_impact = round(contract.base_price * contract.quantity * (obligation.value / 100), 2)
        account = accounts[contract.account_id]
        ai_prediction = explain_prediction(
            contract=contract,
            obligation=obligation,
            days_until_deadline=days_until_deadline,
            predicted_impact=predicted_impact,
        )
        predictions.append(
            RiskPrediction(
                prediction_id=f"prediction-{contract.contract_id}",
                contract_id=contract.contract_id,
                account_id=contract.account_id,
                account_name=account.name,
                risk_type="missed_uplift_risk",
                risk_window_start=as_of,
                risk_window_end=notice_deadline,
                predicted_impact=predicted_impact,
                confidence_score=0.91,
                recommended_action=str(
                    ai_prediction.get("recommended_action")
                    if ai_prediction and ai_prediction.get("recommended_action")
                    else f"Send the uplift notice within {days_until_deadline} days to preserve the upcoming {obligation.value:.0f}% increase."
                ),
                supporting_evidence=(
                    ai_prediction.get("supporting_evidence")
                    if ai_prediction and isinstance(ai_prediction.get("supporting_evidence"), list)
                    else [
                        f"Contract contains a {obligation.value:.0f}% annual uplift clause.",
                        f"Notice deadline is {notice_deadline.isoformat()}.",
                        "No notice_sent event is recorded.",
                    ]
                ),
                days_until_deadline=days_until_deadline,
            )
        )

    return sorted(predictions, key=lambda item: (item.days_until_deadline, -item.predicted_impact))


def get_risk_prediction(prediction_id: str, today: date | None = None) -> RiskPrediction | None:
    for item in get_risk_predictions(today=today):
        if item.prediction_id == prediction_id:
            return item
    return None


def get_dashboard_summary(today: date | None = None) -> DashboardSummary:
    cases = get_leakage_cases(today=today)
    predictions = get_risk_predictions(today=today)
    account_ids = {item.account_id for item in cases} | {item.account_id for item in predictions}

    return DashboardSummary(
        total_estimated_missed_revenue=round(sum(item.estimated_impact for item in cases), 2),
        total_predicted_at_risk_revenue=round(sum(item.predicted_impact for item in predictions), 2),
        flagged_accounts=len(account_ids),
        missed_uplift_cases=len(cases),
        upcoming_risk_cases=len(predictions),
    )
