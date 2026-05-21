from datetime import date

from app.models import ContractDocument, ExtractedObligation
from app.services import leakage
from app.services.document_ingestion import _build_import_impact


def _make_document(*, document_id: str, document_type: str, file_name: str, version: int) -> ContractDocument:
    return ContractDocument(
        document_id=document_id,
        contract_id="ctr-demo",
        document_type=document_type,
        file_name=file_name,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        storage_key=f"contracts/acc-demo/ctr-demo/{file_name}",
        version=version,
        page_count=2,
        ingestion_status="parsed",
    )


def _make_obligation(*, document_id: str | None, value: float, notice_window_days: int, source_clause_text: str) -> ExtractedObligation:
    return ExtractedObligation(
        contract_id="ctr-demo",
        obligation_type="annual_uplift",
        value=value,
        effective_date=date(2026, 1, 1),
        notice_window_days=notice_window_days,
        source_clause_text=source_clause_text,
        confidence_score=0.95,
        document_id=document_id,
        page_number=1,
        extraction_method="ai-docx-native-text",
    )


def test_rule_resolution_prefers_superseding_amendment_when_ai_is_unavailable(monkeypatch) -> None:
    contract = next(item for item in leakage.load_contracts() if item.contract_id == "ctr-1001")
    msa_document = _make_document(
        document_id="doc-msa",
        document_type="msa",
        file_name="northwind-master-subscription-agreement-v1.pdf",
        version=1,
    )
    amendment_document = _make_document(
        document_id="doc-amendment",
        document_type="amendment",
        file_name="northwind-commercial-amendment-v3.docx",
        version=3,
    )
    monkeypatch.setattr(
        leakage,
        "load_contract_documents",
        lambda contract_id=None: [msa_document, amendment_document] if contract_id == contract.contract_id else [],
    )

    resolved = leakage._resolve_annual_uplift_with_rules(
        contract,
        [
            _make_obligation(
                document_id="doc-msa",
                value=5.0,
                notice_window_days=30,
                source_clause_text="The master agreement sets a 5% annual uplift with 30 days notice.",
            ),
            _make_obligation(
                document_id="doc-amendment",
                value=9.0,
                notice_window_days=60,
                source_clause_text="This amendment supersedes prior pricing and sets a 9% annual uplift with 60 days notice.",
            ),
        ],
    )

    assert resolved is not None
    assert resolved.document_id == "doc-amendment"
    assert resolved.value == 9.0
    assert resolved.extraction_method == "rule-resolved-commercial-terms"


def test_build_import_impact_marks_unrelated_upload_as_no_revenue_impact() -> None:
    uploaded_document = _make_document(
        document_id="doc-upload-demo",
        document_type="renewal_notice",
        file_name="customer-qbr-notes.docx",
        version=1,
    )
    governing_document = _make_document(
        document_id="doc-governing",
        document_type="amendment",
        file_name="northwind-commercial-amendment-v2.docx",
        version=2,
    )
    governing_obligation = _make_obligation(
        document_id="doc-governing",
        value=9.0,
        notice_window_days=60,
        source_clause_text="The amendment sets a 9% annual uplift with 60 days notice.",
    )

    impact = _build_import_impact(
        uploaded_document=uploaded_document,
        uploaded_obligations=[],
        previous_obligation=governing_obligation,
        resolved_obligation=governing_obligation,
        documents_by_id={
            uploaded_document.document_id: uploaded_document,
            governing_document.document_id: governing_document,
        },
    )

    assert impact.status == "no_revenue_impact"
    assert "remain unchanged" in impact.summary


def test_build_import_impact_marks_non_controlling_pricing_upload_as_relevant() -> None:
    uploaded_document = _make_document(
        document_id="doc-upload-demo",
        document_type="order_form",
        file_name="northwind-renewal-schedule-v3.pdf",
        version=3,
    )
    governing_document = _make_document(
        document_id="doc-governing",
        document_type="amendment",
        file_name="northwind-commercial-amendment-v2.docx",
        version=2,
    )
    governing_obligation = _make_obligation(
        document_id="doc-governing",
        value=9.0,
        notice_window_days=60,
        source_clause_text="The amendment sets a 9% annual uplift with 60 days notice.",
    )

    impact = _build_import_impact(
        uploaded_document=uploaded_document,
        uploaded_obligations=[
            _make_obligation(
                document_id="doc-upload-demo",
                value=6.0,
                notice_window_days=30,
                source_clause_text="The schedule references a 6% annual uplift with 30 days notice.",
            )
        ],
        previous_obligation=governing_obligation,
        resolved_obligation=governing_obligation,
        documents_by_id={
            uploaded_document.document_id: uploaded_document,
            governing_document.document_id: governing_document,
        },
    )

    assert impact.status == "relevant_non_controlling"
    assert "remains the governing term" in impact.summary


def test_build_import_impact_marks_uploaded_override_as_controlling() -> None:
    uploaded_document = _make_document(
        document_id="doc-upload-demo",
        document_type="amendment",
        file_name="northwind-commercial-amendment-v3.docx",
        version=3,
    )
    previous_obligation = _make_obligation(
        document_id="doc-governing",
        value=8.0,
        notice_window_days=45,
        source_clause_text="The earlier amendment sets an 8% annual uplift with 45 days notice.",
    )
    resolved_obligation = _make_obligation(
        document_id="doc-upload-demo",
        value=10.0,
        notice_window_days=60,
        source_clause_text="This amendment supersedes prior pricing and sets a 10% annual uplift with 60 days notice.",
    )

    impact = _build_import_impact(
        uploaded_document=uploaded_document,
        uploaded_obligations=[resolved_obligation],
        previous_obligation=previous_obligation,
        resolved_obligation=resolved_obligation,
        documents_by_id={uploaded_document.document_id: uploaded_document},
    )

    assert impact.status == "controlling_override"
    assert "Revenue leakage signals were recalculated" in impact.summary