from datetime import date

from app.services import billing_mismatch as billing_svc


def test_billing_mismatch_dashboard_matches_seed_data() -> None:
    dashboard = billing_svc.get_billing_mismatch_dashboard(as_of=date(2026, 5, 1))

    assert dashboard.total_contracts_monitored == 5
    assert dashboard.flagged_contracts == 2
    assert dashboard.total_findings == 7
    assert dashboard.high_severity_findings == 7
    assert dashboard.total_underbilled_amount == 57720.0
    assert dashboard.total_overbilled_amount == 0.0


def test_northwind_analysis_has_expected_underbilled_rate_findings() -> None:
    detail = billing_svc.get_billing_mismatch_analysis("ctr-1001", as_of=date(2026, 5, 1))

    assert detail is not None
    assert detail.analysis.account_name == "Northwind Manufacturing"
    assert detail.analysis.status == "mismatch_detected"
    assert detail.analysis.total_findings == 3
    assert detail.analysis.total_underbilled_amount == 27000.0
    assert len(detail.invoice_reviews) == 4
    assert all(item.mismatch_category == "rate" for item in detail.findings)
    assert all(item.mismatch_direction == "underbilled" for item in detail.findings)
    assert detail.invoice_reviews[-1].expected_unit_price == 109.0
    assert detail.invoice_reviews[-1].actual_unit_price == 100.0


def test_bluepeak_contract_is_aligned_after_uplift_is_applied() -> None:
    detail = billing_svc.get_billing_mismatch_analysis("ctr-1003", as_of=date(2026, 5, 1))

    assert detail is not None
    assert detail.analysis.account_name == "BluePeak Retail"
    assert detail.analysis.status == "aligned"
    assert detail.analysis.total_findings == 0
    assert len(detail.invoice_reviews) == 1
    assert detail.invoice_reviews[0].status == "aligned"
    assert detail.invoice_reviews[0].expected_unit_price == 185.4
    assert detail.invoice_reviews[0].actual_unit_price == 185.4