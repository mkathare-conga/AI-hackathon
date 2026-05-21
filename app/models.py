from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Account(BaseModel):
    account_id: str
    name: str


class Contract(BaseModel):
    contract_id: str
    account_id: str
    product_name: str
    term_start: date
    term_end: date
    base_price: float
    currency: str
    quantity: int = 1
    raw_contract_text: str


class ContractDocument(BaseModel):
    document_id: str
    contract_id: str
    document_type: Literal["msa", "nda", "order_form", "amendment", "renewal_notice"]
    file_name: str
    mime_type: str
    storage_key: str
    version: int
    page_count: int | None = None
    ingestion_status: Literal["pending_upload", "registered", "uploaded", "parsed", "failed"]


class PersistedObligationExtraction(BaseModel):
    extraction_id: str
    contract_id: str
    document_id: str | None = None
    obligation_type: Literal["annual_uplift"]
    value: float
    effective_date: date
    notice_window_days: int
    source_clause_text: str
    page_number: int | None = None
    confidence_score: float
    extraction_method: str


class RenewalEvent(BaseModel):
    contract_id: str
    event_type: Literal["notice_sent", "renewal_started", "renewal_closed"]
    event_date: date


class InvoiceLine(BaseModel):
    invoice_id: str
    account_id: str
    contract_id: str
    billing_period_start: date
    billing_period_end: date
    amount_billed: float
    quantity: int


class ExtractedObligation(BaseModel):
    contract_id: str
    obligation_type: Literal["annual_uplift"]
    value: float
    effective_date: date
    notice_window_days: int
    source_clause_text: str
    confidence_score: float
    document_id: str | None = None
    page_number: int | None = None
    extraction_method: str | None = None


class LeakageCase(BaseModel):
    case_id: str
    contract_id: str
    account_id: str
    account_name: str
    case_type: Literal["missed_uplift"]
    expected_value: float
    actual_value: float
    estimated_impact: float
    confidence_score: float
    explanation: str
    recommended_action: str
    status: Literal["open", "resolved"] = "open"


class RiskPrediction(BaseModel):
    prediction_id: str
    contract_id: str
    account_id: str
    account_name: str
    risk_type: Literal["missed_uplift_risk", "missed_renewal_notice_risk"]
    risk_window_start: date
    risk_window_end: date
    predicted_impact: float
    confidence_score: float
    recommended_action: str
    supporting_evidence: list[str] = Field(default_factory=list)
    days_until_deadline: int


class DashboardSummary(BaseModel):
    total_estimated_missed_revenue: float
    total_predicted_at_risk_revenue: float
    flagged_accounts: int
    missed_uplift_cases: int
    upcoming_risk_cases: int


class AIStatus(BaseModel):
    enabled: bool
    provider: str
    mode: Literal["rule-based-fallback", "model-enhanced"]
    model: str | None = None
    extraction_strategy: str
    explanation_strategy: str


class AIInvestigationBrief(BaseModel):
    focus: Literal["contract", "case", "prediction"]
    generation_mode: Literal["model-generated", "template-fallback"]
    overview: str
    root_cause: str
    recommended_actions: list[str] = Field(default_factory=list)
    evidence_points: list[str] = Field(default_factory=list)
    document_notes: list[str] = Field(default_factory=list)


class DocumentRevenueImpact(BaseModel):
    status: Literal["no_revenue_impact", "relevant_non_controlling", "controlling_override"]
    summary: str
    previous_obligation: ExtractedObligation | None = None
    resolved_obligation: ExtractedObligation | None = None


class DocumentImportResponse(BaseModel):
    document: ContractDocument
    obligations: list[ExtractedObligation] = Field(default_factory=list)
    impact: DocumentRevenueImpact
    message: str


class ContractFactsResponse(BaseModel):
    contract: Contract
    obligations: list[ExtractedObligation]
    candidate_obligations: list[ExtractedObligation] = Field(default_factory=list)
    invoices: list[InvoiceLine]
    renewal_events: list[RenewalEvent]
    documents: list[ContractDocument] = Field(default_factory=list)
