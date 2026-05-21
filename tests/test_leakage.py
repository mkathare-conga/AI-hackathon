from datetime import date

from app.config import clear_ai_settings_cache, clear_data_settings_cache, get_data_settings
from app.models import AIInvestigationBrief, ContractDocument, PersistedObligationExtraction
from app.services.ai_integration import (
    get_ai_status,
    resolve_annual_uplift_from_contract_dossier,
    try_extract_annual_uplift_from_text,
)
from app.services import leakage
from app.services.leakage import (
    UPLIFT_PATTERN,
    _extract_clause_excerpt,
    extract_annual_uplift_from_text,
    get_contract_ai_brief,
    get_contract_facts,
    get_dashboard_summary,
    get_leakage_case,
    get_leakage_cases,
    get_risk_prediction,
    get_risk_predictions,
)


def test_dashboard_summary_has_expected_seed_counts() -> None:
    summary = get_dashboard_summary(today=date(2026, 5, 1))

    assert summary.total_estimated_missed_revenue == 57720.0
    assert summary.total_predicted_at_risk_revenue == 8250.0
    assert summary.flagged_accounts == 4
    assert summary.missed_uplift_cases == 2
    assert summary.upcoming_risk_cases == 2


def test_seed_case_and_prediction_details_are_available() -> None:
    case = get_leakage_case("case-ctr-1001", today=date(2026, 5, 1))
    prediction = get_risk_prediction("prediction-ctr-1002", today=date(2026, 5, 1))
    facts = get_contract_facts("ctr-1001")

    assert case is not None
    assert case.account_name == "Northwind Manufacturing"
    assert case.estimated_impact == 27000.0

    assert prediction is not None
    assert prediction.account_name == "Apex Health Systems"
    assert prediction.days_until_deadline == 17

    assert facts is not None
    assert facts.contract.contract_id == "ctr-1001"
    assert len(facts.obligations) == 1
    assert len(facts.candidate_obligations) == 1
    assert facts.candidate_obligations[0].extraction_method == "regex-contract-text"
    assert facts.documents == []
    assert "REVENUE OPERATIONS DOSSIER SUMMARY" in facts.contract.raw_contract_text
    assert facts.obligations[0].source_clause_text != facts.contract.raw_contract_text
    assert "9% annual uplift" in facts.contract.raw_contract_text


def test_seed_lists_are_sorted_and_non_empty() -> None:
    cases = get_leakage_cases(today=date(2026, 5, 1))
    predictions = get_risk_predictions(today=date(2026, 5, 1))

    assert len(cases) == 2
    assert len(predictions) == 2
    assert cases[0].estimated_impact >= 0
    assert predictions[0].predicted_impact >= 0


def test_clause_excerpt_handles_windows_line_endings() -> None:
    contract_text = (
        "MASTER SUBSCRIPTION AGREEMENT\r\n\r\n"
        "1. Subscription Term. Customer subscribes for an initial term ending December 31, 2025.\r\n\r\n"
        "2. Renewal Pricing Adjustment. Beginning with the first renewal term, fees are subject to a 5% annual price increase with 30 days notice.\r\n\r\n"
        "3. General Terms. This agreement supersedes prior proposals."
    )

    uplift_match = UPLIFT_PATTERN.search(contract_text)

    assert uplift_match is not None
    excerpt = _extract_clause_excerpt(contract_text, uplift_match.start())
    assert excerpt.startswith("2. Renewal Pricing Adjustment.")
    assert "5% annual price increase" in excerpt
    assert "MASTER SUBSCRIPTION AGREEMENT" not in excerpt


def test_extract_annual_uplift_from_text_can_attach_document_metadata() -> None:
    obligations = extract_annual_uplift_from_text(
        contract_id="ctr-uploaded",
        term_start=date(2025, 1, 1),
        contract_text=(
            "Renewal Pricing Adjustment. Beginning with the first renewal term, fees are subject to a 7% annual price increase "
            "with 45 days notice."
        ),
        confidence_score=0.93,
        document_id="doc-uploaded",
        page_number=2,
        extraction_method="pdf-native-text",
    )

    assert len(obligations) == 1
    assert obligations[0].document_id == "doc-uploaded"
    assert obligations[0].page_number == 2
    assert obligations[0].extraction_method == "pdf-native-text"
    assert obligations[0].notice_window_days == 45


def test_persisted_extractions_take_precedence(monkeypatch) -> None:
    contract = next(item for item in leakage.load_contracts() if item.contract_id == "ctr-1001")
    monkeypatch.setattr(
        leakage,
        "load_obligation_extractions",
        lambda contract_id=None: [
            PersistedObligationExtraction(
                extraction_id="ext-1001",
                contract_id="ctr-1001",
                document_id="doc-uploaded",
                obligation_type="annual_uplift",
                value=9.0,
                effective_date=date(2026, 1, 1),
                notice_window_days=60,
                source_clause_text="Uploaded renewal amendment overrides the prior uplift.",
                page_number=1,
                confidence_score=0.99,
                extraction_method="pdf-native-text",
            )
        ]
        if contract_id == "ctr-1001"
        else [],
    )
    monkeypatch.setattr(leakage, "load_contract_documents", lambda contract_id=None: [])
    monkeypatch.setattr(leakage, "try_extract_annual_uplift", lambda contract: None)

    obligations = leakage._extract_annual_uplift(contract, prefer_dossier_resolution=True)

    assert len(obligations) == 1
    assert obligations[0].value == 9.0
    assert obligations[0].document_id == "doc-uploaded"
    assert obligations[0].source_clause_text == "Uploaded renewal amendment overrides the prior uplift."


def test_document_dossier_resolution_overrides_single_source_candidates(monkeypatch) -> None:
    contract = next(item for item in leakage.load_contracts() if item.contract_id == "ctr-1001")
    monkeypatch.setattr(
        leakage,
        "load_obligation_extractions",
        lambda contract_id=None: [
            PersistedObligationExtraction(
                extraction_id="ext-1001",
                contract_id="ctr-1001",
                document_id="doc-amendment-v1",
                obligation_type="annual_uplift",
                value=7.0,
                effective_date=date(2026, 1, 1),
                notice_window_days=30,
                source_clause_text="Older amendment says 7%.",
                page_number=1,
                confidence_score=0.81,
                extraction_method="ai-docx-native-text",
            )
        ]
        if contract_id == "ctr-1001"
        else [],
    )
    monkeypatch.setattr(
        leakage,
        "load_contract_documents",
        lambda contract_id=None: [
            ContractDocument(
                document_id="doc-amendment-v2",
                contract_id="ctr-1001",
                document_type="amendment",
                file_name="northwind-uplift-amendment-v2.docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                storage_key="contracts/acc-1001/ctr-1001/imports/amendment-v2.docx",
                version=2,
                page_count=None,
                ingestion_status="parsed",
            )
        ]
        if contract_id == "ctr-1001"
        else [],
    )
    monkeypatch.setattr(
        leakage,
        "_load_document_text_payload",
        lambda document_id: (
            "Amendment version 2 supersedes prior pricing. Subscription fees are subject to a 9% annual price increase with 60 days notice.",
            None,
            None,
            "docx-native-text",
        ),
    )
    monkeypatch.setattr(
        leakage,
        "resolve_annual_uplift_from_contract_dossier",
        lambda **kwargs: leakage.ExtractedObligation(
            contract_id="ctr-1001",
            obligation_type="annual_uplift",
            value=9.0,
            effective_date=date(2026, 1, 1),
            notice_window_days=60,
            source_clause_text="Amendment version 2 supersedes prior pricing and sets 9% annual uplift.",
            confidence_score=0.96,
            document_id="doc-amendment-v2",
            page_number=None,
            extraction_method="ai-resolved-commercial-terms",
        ),
    )

    obligations = leakage._extract_annual_uplift(contract, prefer_dossier_resolution=True)

    assert len(obligations) == 1
    assert obligations[0].value == 9.0
    assert obligations[0].document_id == "doc-amendment-v2"
    assert obligations[0].extraction_method == "ai-resolved-commercial-terms"


def test_get_contract_facts_prefers_dossier_resolution(monkeypatch) -> None:
    monkeypatch.setattr(
        leakage,
        "_extract_annual_uplift",
        lambda contract, prefer_dossier_resolution=False: [
            leakage.ExtractedObligation(
                contract_id=contract.contract_id,
                obligation_type="annual_uplift",
                value=9.0,
                effective_date=date(2026, 1, 1),
                notice_window_days=60,
                source_clause_text="Resolved across amendment and renewal notice.",
                confidence_score=0.96,
                document_id="doc-upload-e5d45853",
                page_number=None,
                extraction_method="ai-resolved-commercial-terms" if prefer_dossier_resolution else "docx-native-text",
            )
        ],
    )

    facts = get_contract_facts("ctr-1001")

    assert facts is not None
    assert facts.obligations[0].extraction_method == "ai-resolved-commercial-terms"


def test_ai_status_reports_budgeted_explanations_for_github_models(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "github-models")
    monkeypatch.setenv("AI_CHAT_COMPLETIONS_URL", "https://models.github.ai/inference/chat/completions")
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL", "openai/gpt-4.1-mini")
    clear_ai_settings_cache()

    status = get_ai_status()

    assert status.enabled is True
    assert status.explanation_strategy == "model-backed investigation brief with deterministic list copy"


def test_ai_status_defaults_to_rule_based_fallback(monkeypatch) -> None:
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_CHAT_COMPLETIONS_URL", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    clear_ai_settings_cache()

    status = get_ai_status()

    assert status.enabled is False
    assert status.mode == "rule-based-fallback"
    assert status.extraction_strategy == "regex fallback"


def test_ai_status_reports_model_enhanced_when_env_is_configured(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "openai-compatible")
    monkeypatch.setenv("AI_CHAT_COMPLETIONS_URL", "https://example.test/chat/completions")
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL", "gpt-4.1-mini")
    clear_ai_settings_cache()

    status = get_ai_status()

    assert status.enabled is True
    assert status.mode == "model-enhanced"
    assert status.model == "gpt-4.1-mini"


def test_try_extract_annual_uplift_from_text_returns_model_obligation(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ai_integration._chat_completion_json",
        lambda system_prompt, user_prompt: {
            "found": True,
            "uplift_percent": 8,
            "notice_window_days": 45,
            "effective_date": "2026-01-01",
            "source_clause_text": "Renewal fees increase by 8% annually with 45 days notice.",
            "confidence_score": 0.94,
        },
    )

    obligation = try_extract_annual_uplift_from_text(
        contract_id="ctr-1001",
        term_start=date(2025, 1, 1),
        contract_text="Renewal fees increase by 8% annually with 45 days notice.",
        document_id="doc-ai-1",
        page_number=3,
        extraction_method="ai-docx-native-text",
    )

    assert obligation is not None
    assert obligation.contract_id == "ctr-1001"
    assert obligation.value == 8.0
    assert obligation.notice_window_days == 45
    assert obligation.effective_date == date(2026, 1, 1)
    assert obligation.document_id == "doc-ai-1"
    assert obligation.page_number == 3
    assert obligation.extraction_method == "ai-docx-native-text"


def test_resolve_annual_uplift_from_contract_dossier_returns_resolved_obligation(monkeypatch) -> None:
    contract = next(item for item in leakage.load_contracts() if item.contract_id == "ctr-1001")
    monkeypatch.setattr(
        "app.services.ai_integration._chat_completion_json",
        lambda system_prompt, user_prompt: {
            "found": True,
            "uplift_percent": 9,
            "notice_window_days": 60,
            "effective_date": "2026-01-01",
            "source_clause_text": "Amendment v2 supersedes prior pricing and sets a 9% annual uplift.",
            "confidence_score": 0.97,
            "source_document_id": "doc-amendment-v2",
            "page_number": 2,
        },
    )

    obligation = resolve_annual_uplift_from_contract_dossier(
        contract=contract,
        document_sources=[
            {
                "document_id": "doc-amendment-v2",
                "document_type": "amendment",
                "file_name": "northwind-uplift-amendment-v2.docx",
                "version": 2,
                "ingestion_status": "parsed",
                "page_count": None,
                "page_hint": None,
                "text": "This amendment supersedes prior pricing and sets a 9% annual uplift with 60 days notice.",
            }
        ],
        candidate_extractions=[],
    )

    assert obligation is not None
    assert obligation.value == 9.0
    assert obligation.notice_window_days == 60
    assert obligation.document_id == "doc-amendment-v2"
    assert obligation.page_number == 2
    assert obligation.extraction_method == "ai-resolved-commercial-terms"


def test_contract_ai_brief_falls_back_to_template(monkeypatch) -> None:
    monkeypatch.setattr(leakage, "generate_investigation_brief", lambda **kwargs: None)

    brief = get_contract_ai_brief("ctr-1001", focus="case", today=date(2026, 5, 1))

    assert brief is not None
    assert brief.focus == "case"
    assert brief.generation_mode == "template-fallback"
    assert "missed revenue" in brief.overview.lower()
    assert any("9%" in entry for entry in brief.evidence_points)


def test_contract_ai_brief_uses_model_payload_when_available(monkeypatch) -> None:
    monkeypatch.setattr(
        leakage,
        "generate_investigation_brief",
        lambda **kwargs: AIInvestigationBrief(
            focus="case",
            generation_mode="model-generated",
            overview="AI summary",
            root_cause="AI root cause",
            recommended_actions=["Do the thing"],
            evidence_points=["Clause cited"],
            document_notes=["Used the amendment"],
        ),
    )

    brief = get_contract_ai_brief("ctr-1001", focus="case", today=date(2026, 5, 1))

    assert brief is not None
    assert brief.generation_mode == "model-generated"
    assert brief.overview == "AI summary"


def test_data_settings_can_enable_postgres(monkeypatch) -> None:
    monkeypatch.setenv("DATA_SOURCE", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://demo:demo@localhost:5432/demo")
    clear_data_settings_cache()

    settings = get_data_settings()

    assert settings.use_postgres is True
    assert settings.database_url.endswith("/demo")