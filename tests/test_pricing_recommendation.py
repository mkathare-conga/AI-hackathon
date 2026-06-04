from app.services import pricing_recommendation as pricing_svc


def test_pricing_dashboard_returns_same_company_recommendations() -> None:
    pricing_svc.clear_pricing_cache()

    dashboard = pricing_svc.get_pricing_dashboard()
    expected_total = len(pricing_svc.load_open_opportunities())

    assert dashboard.agent_name == "Pre-Sign Pricing Advisor"
    assert dashboard.total_opportunities == expected_total
    assert dashboard.total_opportunities >= 8
    assert len(dashboard.recommendations) == expected_total
    assert dashboard.opportunities_with_price_uplift >= 3
    assert dashboard.total_incremental_annual_contract_value > 0


def test_aldera_recommendation_improves_price_with_reasonable_confidence() -> None:
    pricing_svc.clear_pricing_cache()

    recommendation = next(
        item for item in pricing_svc.list_recommendations()
        if item.account_name == "Aldera Manufacturing Group"
    )

    assert recommendation.recommendation_status == "increase_price"
    assert recommendation.recommended_unit_price > recommendation.current_unit_price
    assert recommendation.trained_deal_count == 5
    assert 0.0 <= recommendation.current_close_confidence <= 1.0
    assert 0.0 <= recommendation.improved_price_close_confidence <= 1.0
    assert recommendation.improved_price_close_confidence >= 0.55
    assert recommendation.incremental_annual_contract_value > 0
    assert len(recommendation.comparable_deals) == 3
    assert recommendation.same_company_win_rate >= 0.6


def test_pricing_floor_never_exceeds_recommended_price() -> None:
    pricing_svc.clear_pricing_cache()

    recommendations = pricing_svc.list_recommendations()

    assert recommendations
    assert all(item.minimum_floor_unit_price <= item.recommended_unit_price for item in recommendations)