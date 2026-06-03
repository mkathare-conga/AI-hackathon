"""Data models for the Billing vs Contract Mismatch agent."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BillingInvoiceReview(BaseModel):
    invoice_id: str
    billing_period_start: date
    billing_period_end: date
    expected_unit_price: float
    actual_unit_price: float
    expected_quantity: int
    actual_quantity: int
    expected_amount: float
    actual_amount: float
    net_variance_amount: float
    status: Literal["aligned", "underbilled", "overbilled"]


class BillingMismatchFinding(BaseModel):
    finding_id: str
    contract_id: str
    invoice_id: str
    mismatch_category: Literal["rate", "quantity"]
    mismatch_direction: Literal["underbilled", "overbilled"]
    severity: Literal["high", "medium", "low"]
    billing_period_start: date
    billing_period_end: date
    expected_unit_price: float
    actual_unit_price: float
    expected_quantity: int
    actual_quantity: int
    expected_amount: float
    actual_amount: float
    variance_amount: float
    variance_percent: float
    explanation: str
    recommended_action: str
    source_clause_text: str | None = None
    confidence_score: float = 0.95


class BillingMismatchAnalysis(BaseModel):
    analysis_id: str
    contract_id: str
    account_id: str
    account_name: str
    product_name: str
    status: Literal["aligned", "mismatch_detected"]
    total_invoices_reviewed: int
    total_findings: int
    high_severity_count: int
    total_underbilled_amount: float
    total_overbilled_amount: float
    latest_billing_period_end: date | None = None
    latest_expected_amount: float | None = None
    latest_actual_amount: float | None = None
    latest_expected_unit_price: float | None = None
    latest_actual_unit_price: float | None = None
    governing_clause_excerpt: str | None = None


class BillingMismatchAnalysisDetail(BaseModel):
    analysis: BillingMismatchAnalysis
    invoice_reviews: list[BillingInvoiceReview] = Field(default_factory=list)
    findings: list[BillingMismatchFinding] = Field(default_factory=list)


class BillingMismatchDashboard(BaseModel):
    total_contracts_monitored: int
    flagged_contracts: int
    total_findings: int
    high_severity_findings: int
    total_underbilled_amount: float
    total_overbilled_amount: float
    analyses: list[BillingMismatchAnalysisDetail] = Field(default_factory=list)