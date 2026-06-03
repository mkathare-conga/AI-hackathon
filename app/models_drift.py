"""Data models for the Quote-to-Contract Drift Detector agent."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Quote(BaseModel):
    quote_id: str
    account_name: str
    opportunity_name: str
    created_date: date
    status: str = "approved"


class QuoteLine(BaseModel):
    line_id: str
    quote_id: str
    product_name: str
    quantity: int
    unit_price: float
    discount_percent: float = 0
    support_tier: str = "standard"
    renewal_uplift_percent: float | None = None
    payment_terms_days: int = 30
    currency: str = "USD"


class DriftContract(BaseModel):
    contract_id: str
    quote_id: str
    contract_text: str
    signed_date: date


class DriftFinding(BaseModel):
    finding_id: str
    quote_id: str
    contract_id: str
    drift_type: Literal["price", "quantity", "scope", "support", "payment_terms", "renewal_terms"]
    attribute_name: str
    quote_value: str
    contract_value: str
    severity: Literal["high", "medium", "low"]
    estimated_annual_impact: float | None = None
    explanation: str
    source_clause_text: str | None = None
    confidence_score: float = 0.9


class DriftAnalysisRequest(BaseModel):
    quote_id: str
    contract_id: str


class DriftSummary(BaseModel):
    quote_id: str
    contract_id: str
    account_name: str
    opportunity_name: str
    total_findings: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    total_estimated_annual_impact: float
    findings: list[DriftFinding] = Field(default_factory=list)


class DriftDashboard(BaseModel):
    total_quotes_analyzed: int
    total_findings: int
    total_high_severity: int
    total_estimated_impact: float
    analyses: list[DriftSummary] = Field(default_factory=list)
