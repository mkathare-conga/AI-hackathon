"""Data models for the Pre-Sign Pricing Advisor agent."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class PricingHistoricalDeal(BaseModel):
    deal_id: str
    account_name: str
    product_name: str
    outcome: Literal["won", "lost"]
    list_unit_price: float
    final_unit_price: float
    quantity: int
    term_months: int
    support_tier: Literal["standard", "premium"]
    procurement_rigor: Literal["low", "medium", "high"]
    strategic: bool = False
    signed_date: date
    competitor: str | None = None
    notes: str | None = None


class PricingOpportunity(BaseModel):
    opportunity_id: str
    account_name: str
    opportunity_name: str
    product_name: str
    stage: Literal["proposal", "redline", "final_review"]
    list_unit_price: float
    current_unit_price: float
    quantity: int
    term_months: int
    support_tier: Literal["standard", "premium"]
    procurement_rigor: Literal["low", "medium", "high"]
    strategic: bool = False
    currency: str = "USD"
    close_target_date: date


class PricingComparableDeal(BaseModel):
    deal_id: str
    account_name: str
    signed_date: date
    outcome: Literal["won", "lost"]
    final_unit_price: float
    discount_percent: float
    quantity: int
    term_months: int
    support_tier: Literal["standard", "premium"]
    notes: str | None = None


class PricingRecommendation(BaseModel):
    recommendation_id: str
    opportunity_id: str
    account_name: str
    opportunity_name: str
    product_name: str
    stage: Literal["proposal", "redline", "final_review"]
    currency: str = "USD"
    recommendation_status: Literal["increase_price", "hold_price"]
    current_unit_price: float
    recommended_unit_price: float
    minimum_floor_unit_price: float
    current_discount_percent: float
    recommended_discount_percent: float
    current_annual_contract_value: float
    recommended_annual_contract_value: float
    incremental_annual_contract_value: float
    current_total_contract_value: float
    recommended_total_contract_value: float
    incremental_total_contract_value: float
    current_close_confidence: float
    improved_price_close_confidence: float
    approval_path: str
    trained_deal_count: int
    same_company_win_rate: float
    recommended_actions: list[str] = Field(default_factory=list)
    model_highlights: list[str] = Field(default_factory=list)
    important_signing_considerations: list[str] = Field(default_factory=list)
    comparable_deals: list[PricingComparableDeal] = Field(default_factory=list)


class PricingDashboard(BaseModel):
    agent_name: str
    agent_description: str
    total_opportunities: int
    opportunities_with_price_uplift: int
    total_incremental_annual_contract_value: float
    average_improved_close_confidence: float
    recommendations: list[PricingRecommendation] = Field(default_factory=list)