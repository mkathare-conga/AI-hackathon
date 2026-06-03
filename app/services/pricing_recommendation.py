"""Pre-Sign Pricing Advisor — recommend stronger pricing from same-company deal history."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from statistics import mean

from app.models_pricing import (
    PricingComparableDeal,
    PricingDashboard,
    PricingHistoricalDeal,
    PricingOpportunity,
    PricingRecommendation,
)


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic" / "pricing_recommendation"
AGENT_NAME = "Pre-Sign Pricing Advisor"
AGENT_DESCRIPTION = (
    "Uses same-company historical deal outcomes to recommend stronger pre-sign pricing, "
    "showing the safer improved price, expected commercial lift, and close confidence tradeoff before signature."
)
PROCUREMENT_RANK = {"low": 0, "medium": 1, "high": 2}


def _load_json_file(name: str) -> list[dict]:
    file_path = DATA_DIR / name
    with file_path.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list payload in {name}")
    return payload


@lru_cache(maxsize=1)
def load_historical_deals() -> list[PricingHistoricalDeal]:
    return [PricingHistoricalDeal.model_validate(item) for item in _load_json_file("historical_deals.json")]


@lru_cache(maxsize=1)
def load_open_opportunities() -> list[PricingOpportunity]:
    return [PricingOpportunity.model_validate(item) for item in _load_json_file("open_opportunities.json")]


def _discount_percent(list_unit_price: float, final_unit_price: float) -> float:
    if list_unit_price <= 0:
        return 0.0
    return round((1 - (final_unit_price / list_unit_price)) * 100, 1)


def _effective_price_ratio(final_unit_price: float, list_unit_price: float) -> float:
    if list_unit_price <= 0:
        return 0.0
    return final_unit_price / list_unit_price


def _company_history_for_opportunity(opportunity: PricingOpportunity) -> list[PricingHistoricalDeal]:
    exact_product = [
        item for item in load_historical_deals()
        if item.account_name == opportunity.account_name and item.product_name == opportunity.product_name
    ]
    if len(exact_product) >= 2:
        return exact_product

    same_company = [item for item in load_historical_deals() if item.account_name == opportunity.account_name]
    if same_company:
        return same_company

    return load_historical_deals()


def _similarity(opportunity: PricingOpportunity, deal: PricingHistoricalDeal) -> float:
    quantity_delta = abs(math.log((deal.quantity + 1) / (opportunity.quantity + 1)))
    term_delta = abs(deal.term_months - opportunity.term_months) / 12
    support_penalty = 0.0 if deal.support_tier == opportunity.support_tier else 0.35
    procurement_penalty = abs(PROCUREMENT_RANK[deal.procurement_rigor] - PROCUREMENT_RANK[opportunity.procurement_rigor]) * 0.2
    strategic_bonus = 0.08 if deal.strategic == opportunity.strategic else -0.04
    return math.exp(-(quantity_delta * 0.6 + term_delta * 0.4 + support_penalty + procurement_penalty) + strategic_bonus)


def _weighted_close_confidence(
    opportunity: PricingOpportunity,
    history: list[PricingHistoricalDeal],
    candidate_unit_price: float,
) -> float:
    candidate_ratio = _effective_price_ratio(candidate_unit_price, opportunity.list_unit_price)
    weighted_wins = 0.0
    weighted_total = 0.0

    for deal in history:
        price_gap = abs(_effective_price_ratio(deal.final_unit_price, deal.list_unit_price) - candidate_ratio)
        price_weight = math.exp(-(price_gap * 18))
        weight = _similarity(opportunity, deal) * price_weight
        weighted_total += weight
        if deal.outcome == "won":
            weighted_wins += weight

    company_win_rate = mean(1.0 if deal.outcome == "won" else 0.0 for deal in history) if history else 0.5
    base_probability = (weighted_wins / weighted_total) if weighted_total else company_win_rate

    if opportunity.strategic:
        base_probability += 0.03
    if opportunity.procurement_rigor == "high":
        base_probability -= 0.04
    elif opportunity.procurement_rigor == "medium":
        base_probability -= 0.02

    return round(min(0.95, max(0.1, base_probability)), 2)


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = max(0.0, min(1.0, percentile)) * (len(sorted_values) - 1)
    lower_index = int(math.floor(position))
    upper_index = int(math.ceil(position))
    if lower_index == upper_index:
        return sorted_values[lower_index]
    fraction = position - lower_index
    return sorted_values[lower_index] + ((sorted_values[upper_index] - sorted_values[lower_index]) * fraction)


def _safe_upper_ratio(history: list[PricingHistoricalDeal], current_ratio: float) -> float:
    won_ratios = sorted(
        _effective_price_ratio(item.final_unit_price, item.list_unit_price)
        for item in history
        if item.outcome == "won"
    )
    if not won_ratios:
        return current_ratio

    target_ratio = _percentile(won_ratios, 0.65)
    stretch_ratio = _percentile(won_ratios, 0.85)
    risky_lost_ratios = sorted(
        _effective_price_ratio(item.final_unit_price, item.list_unit_price)
        for item in history
        if item.outcome == "lost" and _effective_price_ratio(item.final_unit_price, item.list_unit_price) >= target_ratio
    )

    safe_ratio = stretch_ratio
    if risky_lost_ratios:
        safe_ratio = min(safe_ratio, risky_lost_ratios[0] - 0.005)

    safe_ratio = max(current_ratio, max(target_ratio, safe_ratio))
    return round(min(0.99, safe_ratio), 4)


def _build_comparable_deals(
    opportunity: PricingOpportunity,
    history: list[PricingHistoricalDeal],
) -> list[PricingComparableDeal]:
    ranked = sorted(history, key=lambda item: _similarity(opportunity, item), reverse=True)
    return [
        PricingComparableDeal(
            deal_id=item.deal_id,
            account_name=item.account_name,
            signed_date=item.signed_date,
            outcome=item.outcome,
            final_unit_price=item.final_unit_price,
            discount_percent=_discount_percent(item.list_unit_price, item.final_unit_price),
            quantity=item.quantity,
            term_months=item.term_months,
            support_tier=item.support_tier,
            notes=item.notes,
        )
        for item in ranked[:3]
    ]


def _approval_path(current_discount_percent: float, recommended_discount_percent: float) -> str:
    if recommended_discount_percent <= 8:
        return "Standard pricing approval"
    if recommended_discount_percent <= 15:
        return "Commercial manager review"
    if recommended_discount_percent < current_discount_percent:
        return "Director approval for final discount exception"
    return "Executive pricing approval"


def _build_recommendation(opportunity: PricingOpportunity) -> PricingRecommendation:
    history = _company_history_for_opportunity(opportunity)
    current_ratio = _effective_price_ratio(opportunity.current_unit_price, opportunity.list_unit_price)
    current_close_confidence = _weighted_close_confidence(opportunity, history, opportunity.current_unit_price)
    target_confidence_floor = max(0.55, current_close_confidence - 0.08)
    max_ratio = _safe_upper_ratio(history, current_ratio)

    best_ratio = current_ratio
    best_confidence = current_close_confidence

    for step in range(1, 13):
        candidate_ratio = current_ratio + ((max_ratio - current_ratio) * (step / 12))
        candidate_unit_price = opportunity.list_unit_price * candidate_ratio
        candidate_confidence = _weighted_close_confidence(opportunity, history, candidate_unit_price)
        if candidate_confidence >= target_confidence_floor:
            best_ratio = candidate_ratio
            best_confidence = candidate_confidence

    recommended_unit_price = round(opportunity.list_unit_price * best_ratio, 2)
    current_discount_percent = _discount_percent(opportunity.list_unit_price, opportunity.current_unit_price)
    recommended_discount_percent = _discount_percent(opportunity.list_unit_price, recommended_unit_price)

    raw_floor_unit_price = round(opportunity.list_unit_price * max(current_ratio, _percentile(sorted(
        _effective_price_ratio(item.final_unit_price, item.list_unit_price)
        for item in history if item.outcome == "won"
    ), 0.35)), 2)
    minimum_floor_unit_price = min(raw_floor_unit_price, recommended_unit_price)

    current_annual_contract_value = round(opportunity.current_unit_price * opportunity.quantity * 12, 2)
    recommended_annual_contract_value = round(recommended_unit_price * opportunity.quantity * 12, 2)
    current_total_contract_value = round(opportunity.current_unit_price * opportunity.quantity * opportunity.term_months, 2)
    recommended_total_contract_value = round(recommended_unit_price * opportunity.quantity * opportunity.term_months, 2)
    same_company_win_rate = round(mean(1.0 if item.outcome == "won" else 0.0 for item in history), 2)

    comparable_deals = _build_comparable_deals(opportunity, history)
    recommendation_status = "increase_price" if recommended_unit_price > opportunity.current_unit_price else "hold_price"

    recommended_actions = [
        f"Open the final paper at {opportunity.currency} {recommended_unit_price:.2f} per unit instead of {opportunity.currency} {opportunity.current_unit_price:.2f}.",
        f"Hold a walk-away floor of {opportunity.currency} {minimum_floor_unit_price:.2f} per unit during redlines.",
        "Trade term length or support concessions before giving additional unit-price discount.",
    ]
    model_highlights = [
        f"Model trained on {len(history)} prior {opportunity.account_name} deals for this recommendation.",
        f"Same-company win rate is {round(same_company_win_rate * 100)}% across the training sample.",
        f"Improved pricing keeps projected close confidence at {round(best_confidence * 100)}%.",
    ]
    important_signing_considerations = [
        f"Current discount is {current_discount_percent:.1f}%; recommended discount is {recommended_discount_percent:.1f}%.",
        f"Procurement rigor is rated {opportunity.procurement_rigor}, so approval timing should be built into signature planning.",
        f"{len(comparable_deals)} closest same-company deals were used as comparables before final papering.",
    ]

    return PricingRecommendation(
        recommendation_id=f"pricing-{opportunity.opportunity_id}",
        opportunity_id=opportunity.opportunity_id,
        account_name=opportunity.account_name,
        opportunity_name=opportunity.opportunity_name,
        product_name=opportunity.product_name,
        stage=opportunity.stage,
        currency=opportunity.currency,
        recommendation_status=recommendation_status,
        current_unit_price=opportunity.current_unit_price,
        recommended_unit_price=recommended_unit_price,
        minimum_floor_unit_price=minimum_floor_unit_price,
        current_discount_percent=current_discount_percent,
        recommended_discount_percent=recommended_discount_percent,
        current_annual_contract_value=current_annual_contract_value,
        recommended_annual_contract_value=recommended_annual_contract_value,
        incremental_annual_contract_value=round(recommended_annual_contract_value - current_annual_contract_value, 2),
        current_total_contract_value=current_total_contract_value,
        recommended_total_contract_value=recommended_total_contract_value,
        incremental_total_contract_value=round(recommended_total_contract_value - current_total_contract_value, 2),
        current_close_confidence=current_close_confidence,
        improved_price_close_confidence=best_confidence,
        approval_path=_approval_path(current_discount_percent, recommended_discount_percent),
        trained_deal_count=len(history),
        same_company_win_rate=same_company_win_rate,
        recommended_actions=recommended_actions,
        model_highlights=model_highlights,
        important_signing_considerations=important_signing_considerations,
        comparable_deals=comparable_deals,
    )


@lru_cache(maxsize=1)
def list_recommendations() -> list[PricingRecommendation]:
    recommendations = [_build_recommendation(opportunity) for opportunity in load_open_opportunities()]
    return sorted(recommendations, key=lambda item: item.incremental_annual_contract_value, reverse=True)


def get_recommendation(recommendation_id: str) -> PricingRecommendation | None:
    for item in list_recommendations():
        if item.recommendation_id == recommendation_id:
            return item
    return None


def get_pricing_dashboard() -> PricingDashboard:
    recommendations = list_recommendations()
    return PricingDashboard(
        agent_name=AGENT_NAME,
        agent_description=AGENT_DESCRIPTION,
        total_opportunities=len(recommendations),
        opportunities_with_price_uplift=sum(1 for item in recommendations if item.recommendation_status == "increase_price"),
        total_incremental_annual_contract_value=round(sum(item.incremental_annual_contract_value for item in recommendations), 2),
        average_improved_close_confidence=round(mean(item.improved_price_close_confidence for item in recommendations), 2),
        recommendations=recommendations,
    )


def clear_pricing_cache() -> None:
    load_historical_deals.cache_clear()
    load_open_opportunities.cache_clear()
    list_recommendations.cache_clear()