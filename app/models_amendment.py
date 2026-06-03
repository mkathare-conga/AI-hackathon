"""Data models for the Amendment Impact Detector agent."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AmendmentAnalysis(BaseModel):
    analysis_id: str
    contract_id: str
    account_name: str
    amendment_summary: str
    amendment_date: date
    total_changes: int = 0
    high_impact_count: int = 0
    total_annual_revenue_delta: float = 0
    status: Literal["pending", "analyzed", "acknowledged"] = "analyzed"


class AmendmentImpact(BaseModel):
    impact_id: str
    analysis_id: str
    contract_id: str
    impact_category: Literal[
        "pricing_change", "quantity_change", "term_extension", "term_reduction",
        "support_change", "scope_addition", "scope_removal", "renewal_terms_change",
        "payment_terms_change", "liability_change", "sla_change"
    ]
    before_value: str
    after_value: str
    severity: Literal["high", "medium", "low"]
    annual_revenue_delta: float | None = None
    requires_billing_update: bool = False
    requires_workflow_update: bool = False
    explanation: str
    source_clause_text: str | None = None
    confidence_score: float = 0.9


class AmendmentActionItem(BaseModel):
    action_id: str
    analysis_id: str
    impact_id: str | None = None
    action_type: Literal[
        "update_billing", "update_renewal_workflow", "notify_customer",
        "update_support_tier", "review_sla", "update_provisioning", "legal_review"
    ]
    description: str
    priority: Literal["urgent", "high", "medium", "low"]
    status: Literal["open", "in_progress", "completed", "dismissed"] = "open"
    assigned_team: str | None = None


class AmendmentAnalysisDetail(BaseModel):
    analysis: AmendmentAnalysis
    impacts: list[AmendmentImpact] = Field(default_factory=list)
    action_items: list[AmendmentActionItem] = Field(default_factory=list)


class AmendmentDashboard(BaseModel):
    total_analyses: int
    total_impacts: int
    total_action_items_open: int
    net_annual_revenue_delta: float
    positive_amendments: int
    negative_amendments: int
    analyses: list[AmendmentAnalysisDetail] = Field(default_factory=list)
