from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from app.config import get_data_settings, get_object_store_settings
from app.data_loader import load_contract_documents, load_contracts
from app.models import Contract, ContractDocument, DocumentImportResponse, DocumentRevenueImpact, ExtractedObligation
from app.object_store import get_minio_client
from app.services.ai_integration import try_extract_annual_uplift_from_text
from app.services.document_text import MIME_BY_SUFFIX, extract_document_text
from app.services.leakage import (
    UPLIFT_PATTERN,
    _extract_relevant_excerpt,
    clear_leakage_resolution_caches,
    extract_annual_uplift_from_text,
    get_governing_annual_uplift,
)


def _sanitize_file_name(file_name: str) -> str:
    sanitized_name = Path(file_name or "uploaded-document").name.strip()
    return sanitized_name or "uploaded-document"


def _resolve_contract(contract_id: str) -> Contract:
    contract = next((item for item in load_contracts() if item.contract_id == contract_id), None)
    if contract is None:
        raise ValueError("Contract not found")
    return contract


def _resolve_mime_type(file_name: str, content_type: str | None) -> tuple[str, str]:
    suffix = Path(file_name).suffix.lower()
    inferred_mime_type = MIME_BY_SUFFIX.get(suffix)
    if inferred_mime_type is None:
        raise ValueError("Only PDF and DOCX files are supported for import")

    normalized_content_type = (content_type or "").strip().lower()
    if normalized_content_type and normalized_content_type != "application/octet-stream":
        allowed_types = {inferred_mime_type}
        if inferred_mime_type == MIME_BY_SUFFIX[".docx"]:
            allowed_types.add("application/msword")
        if normalized_content_type not in allowed_types:
            raise ValueError("Uploaded file content type does not match the selected document format")

    return inferred_mime_type, suffix


def _next_document_version(contract_id: str, document_type: str) -> int:
    current_versions = [
        document.version for document in load_contract_documents(contract_id=contract_id) if document.document_type == document_type
    ]
    return (max(current_versions) if current_versions else 0) + 1


def _same_obligation_terms(left: ExtractedObligation | None, right: ExtractedObligation | None) -> bool:
    if left is None or right is None:
        return False

    return (
        left.value == right.value
        and left.notice_window_days == right.notice_window_days
        and left.effective_date == right.effective_date
    )


def _format_obligation_summary(
    obligation: ExtractedObligation | None,
    documents_by_id: dict[str, ContractDocument],
) -> str:
    if obligation is None:
        return "no governing uplift term"

    if obligation.document_id:
        source_name = documents_by_id.get(obligation.document_id)
        source_label = source_name.file_name if source_name is not None else obligation.document_id
    else:
        source_label = "the contract record"

    return (
        f"{obligation.value:.0f}% uplift effective {obligation.effective_date.isoformat()} "
        f"with {obligation.notice_window_days} days notice from {source_label}"
    )


def _build_import_impact(
    *,
    uploaded_document: ContractDocument,
    uploaded_obligations: list[ExtractedObligation],
    previous_obligation: ExtractedObligation | None,
    resolved_obligation: ExtractedObligation | None,
    documents_by_id: dict[str, ContractDocument],
) -> DocumentRevenueImpact:
    uploaded_label = uploaded_document.file_name

    if not uploaded_obligations:
        summary = (
            f"{uploaded_label} was analyzed, but no pricing, uplift, renewal, or notice clause was found. "
            "Revenue leakage signals remain unchanged."
        )
        return DocumentRevenueImpact(
            status="no_revenue_impact",
            summary=summary,
            previous_obligation=previous_obligation,
            resolved_obligation=resolved_obligation,
        )

    if resolved_obligation is None:
        summary = (
            f"{uploaded_label} was analyzed and contains revenue-related language, but the contract no longer has a resolved governing uplift term. "
            "Revenue leakage signals were cleared."
        )
        return DocumentRevenueImpact(
            status="controlling_override",
            summary=summary,
            previous_obligation=previous_obligation,
            resolved_obligation=resolved_obligation,
        )

    current_summary = _format_obligation_summary(resolved_obligation, documents_by_id)
    previous_summary = _format_obligation_summary(previous_obligation, documents_by_id)

    if resolved_obligation.document_id == uploaded_document.document_id:
        if previous_obligation is not None and _same_obligation_terms(previous_obligation, resolved_obligation):
            summary = (
                f"{uploaded_label} becomes the latest governing source of record for {current_summary}, "
                "but the governing economics did not change, so revenue leakage signals remain unchanged."
            )
            status = "relevant_non_controlling"
        else:
            prefix = "established" if previous_obligation is None else f"overrides the prior governing term of {previous_summary} and sets"
            summary = (
                f"{uploaded_label} {prefix} {current_summary}. Revenue leakage signals were recalculated."
            )
            status = "controlling_override"

        return DocumentRevenueImpact(
            status=status,
            summary=summary,
            previous_obligation=previous_obligation,
            resolved_obligation=resolved_obligation,
        )

    if previous_obligation is not None and _same_obligation_terms(previous_obligation, resolved_obligation):
        summary = (
            f"{uploaded_label} contains pricing-related language, but {current_summary} remains the governing term. "
            "Revenue leakage signals remain unchanged."
        )
        status = "relevant_non_controlling"
    else:
        summary = (
            f"{uploaded_label} changed the governing revenue term to {current_summary}. "
            "Revenue leakage signals were recalculated."
        )
        status = "controlling_override"

    return DocumentRevenueImpact(
        status=status,
        summary=summary,
        previous_obligation=previous_obligation,
        resolved_obligation=resolved_obligation,
    )


def import_contract_document(
    *,
    contract_id: str,
    document_type: str,
    file_name: str,
    content_type: str | None,
    payload: bytes,
) -> DocumentImportResponse:
    if not payload:
        raise ValueError("Uploaded file is empty")

    settings = get_data_settings()
    if not settings.use_postgres:
        raise RuntimeError("Document import requires DATA_SOURCE=postgres")
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured for document import")

    contract = _resolve_contract(contract_id)
    previous_obligation = get_governing_annual_uplift(contract.contract_id)
    safe_file_name = _sanitize_file_name(file_name)
    mime_type, suffix = _resolve_mime_type(safe_file_name, content_type)
    version = _next_document_version(contract_id, document_type)
    document_id = f"doc-upload-{uuid4().hex[:8]}"
    storage_key = f"contracts/{contract.account_id}/{contract.contract_id}/imports/{document_type}-v{version}-{uuid4().hex[:8]}{suffix}"

    extracted_text, page_count, page_number, extraction_method = extract_document_text(
        mime_type,
        payload,
        page_hint_pattern=UPLIFT_PATTERN,
    )
    ai_obligation = try_extract_annual_uplift_from_text(
        contract_id=contract.contract_id,
        term_start=contract.term_start,
        contract_text=extracted_text,
        document_id=document_id,
        page_number=page_number,
        extraction_method=f"ai-{extraction_method}",
    )
    obligations = [ai_obligation] if ai_obligation is not None else extract_annual_uplift_from_text(
        contract_id=contract.contract_id,
        term_start=contract.term_start,
        contract_text=extracted_text,
        confidence_score=0.93,
        document_id=document_id,
        page_number=page_number,
        extraction_method=extraction_method,
    )
    ingestion_status = "parsed" if obligations else "uploaded"

    client = get_minio_client()
    bucket_name = get_object_store_settings().bucket_name
    client.put_object(
        bucket_name,
        storage_key,
        BytesIO(payload),
        length=len(payload),
        content_type=mime_type,
    )

    try:
        import psycopg

        commercial_excerpt = _extract_relevant_excerpt(extracted_text) if extracted_text else None

        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    (
                        "INSERT INTO contract_documents "
                        "(document_id, contract_id, document_type, file_name, mime_type, storage_key, version, page_count, extracted_text, commercial_excerpt, ingestion_status) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    ),
                    (
                        document_id,
                        contract.contract_id,
                        document_type,
                        safe_file_name,
                        mime_type,
                        storage_key,
                        version,
                        page_count,
                        extracted_text,
                        commercial_excerpt,
                        ingestion_status,
                    ),
                )
                for obligation in obligations:
                    cursor.execute(
                        (
                            "INSERT INTO obligation_extractions "
                            "(extraction_id, contract_id, document_id, obligation_type, value, effective_date, notice_window_days, source_clause_text, page_number, confidence_score, extraction_method) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        ),
                        (
                            f"ext-{uuid4().hex[:12]}",
                            obligation.contract_id,
                            document_id,
                            obligation.obligation_type,
                            obligation.value,
                            obligation.effective_date,
                            obligation.notice_window_days,
                            obligation.source_clause_text,
                            obligation.page_number,
                            obligation.confidence_score,
                            obligation.extraction_method or extraction_method,
                        ),
                    )
            connection.commit()
    except Exception:
        client.remove_object(bucket_name, storage_key)
        raise

    document = ContractDocument(
        document_id=document_id,
        contract_id=contract.contract_id,
        document_type=document_type,
        file_name=safe_file_name,
        mime_type=mime_type,
        storage_key=storage_key,
        version=version,
        page_count=page_count,
        ingestion_status=ingestion_status,
    )
    clear_leakage_resolution_caches()
    resolved_obligation = get_governing_annual_uplift(contract.contract_id)
    documents_by_id = {
        existing_document.document_id: existing_document
        for existing_document in load_contract_documents(contract_id=contract.contract_id)
    }
    impact = _build_import_impact(
        uploaded_document=document,
        uploaded_obligations=obligations,
        previous_obligation=previous_obligation,
        resolved_obligation=resolved_obligation,
        documents_by_id=documents_by_id,
    )
    return DocumentImportResponse(
        document=document,
        obligations=obligations,
        impact=impact,
        message=impact.summary,
    )