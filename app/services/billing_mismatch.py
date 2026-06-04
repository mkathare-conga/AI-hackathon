"""Billing vs Contract Mismatch — compare invoice feeds to contract terms."""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from app.data_loader import load_accounts, load_contracts, load_invoice_lines
from app.models import Contract, InvoiceLine
from app.models_billing import (
    BillingInvoiceReview,
    BillingMismatchAnalysis,
    BillingMismatchAnalysisDetail,
    BillingMismatchDashboard,
    BillingMismatchFinding,
)
from app.services.leakage import get_governing_annual_uplift


RATE_TOLERANCE = 0.01


def _group_invoices(as_of: date) -> dict[str, list[InvoiceLine]]:
    grouped: dict[str, list[InvoiceLine]] = defaultdict(list)
    for invoice in load_invoice_lines():
        if invoice.billing_period_start <= as_of:
            grouped[invoice.contract_id].append(invoice)

    for rows in grouped.values():
        rows.sort(key=lambda item: item.billing_period_start)
    return grouped


def _actual_unit_price(invoice: InvoiceLine) -> float:
    if invoice.quantity <= 0:
        return 0.0
    return round(invoice.amount_billed / invoice.quantity, 2)


def _expected_unit_price(contract: Contract, invoice: InvoiceLine) -> tuple[float, str | None]:
    obligation = get_governing_annual_uplift(contract.contract_id)
    if obligation is not None and invoice.billing_period_start >= obligation.effective_date:
        uplifted_price = round(contract.base_price * (1 + (obligation.value / 100)), 2)
        return uplifted_price, obligation.source_clause_text
    return round(contract.base_price, 2), None


def _variance_percent(actual_value: float, expected_value: float) -> float:
    if expected_value == 0:
        return 0.0
    return round(((actual_value - expected_value) / expected_value) * 100, 1)


def _severity(variance_amount: float, variance_percent: float) -> str:
    absolute_amount = abs(variance_amount)
    absolute_percent = abs(variance_percent)
    if absolute_amount >= 5000 or absolute_percent >= 5:
        return "high"
    if absolute_amount >= 1000 or absolute_percent >= 2:
        return "medium"
    return "low"


def _invoice_status(net_variance_amount: float) -> str:
    if net_variance_amount < -RATE_TOLERANCE:
        return "underbilled"
    if net_variance_amount > RATE_TOLERANCE:
        return "overbilled"
    return "aligned"


def _rate_action(direction: str) -> str:
    if direction == "underbilled":
        return "Update the billing rate card to the contracted unit price and issue a catch-up invoice if appropriate."
    return "Review the invoice for overbilling and determine whether a credit or corrected bill is required."


def _quantity_action(direction: str) -> str:
    if direction == "underbilled":
        return "Reconcile the billed quantity with the contracted commitment and update provisioning or billing counts."
    return "Confirm the overage was contractually approved before billing above the committed quantity."


def _build_rate_finding(
    contract: Contract,
    invoice: InvoiceLine,
    expected_unit_price: float,
    actual_unit_price: float,
    expected_amount: float,
    clause_excerpt: str | None,
) -> BillingMismatchFinding:
    component_variance = round((actual_unit_price - expected_unit_price) * invoice.quantity, 2)
    variance_percent = _variance_percent(actual_unit_price, expected_unit_price)
    direction = "underbilled" if component_variance < 0 else "overbilled"
    return BillingMismatchFinding(
        finding_id=f"billing-rate-{invoice.invoice_id}",
        contract_id=contract.contract_id,
        invoice_id=invoice.invoice_id,
        mismatch_category="rate",
        mismatch_direction=direction,
        severity=_severity(component_variance, variance_percent),
        billing_period_start=invoice.billing_period_start,
        billing_period_end=invoice.billing_period_end,
        expected_unit_price=expected_unit_price,
        actual_unit_price=actual_unit_price,
        expected_quantity=contract.quantity,
        actual_quantity=invoice.quantity,
        expected_amount=expected_amount,
        actual_amount=invoice.amount_billed,
        variance_amount=component_variance,
        variance_percent=variance_percent,
        explanation=(
            f"Invoice {invoice.invoice_id} billed {actual_unit_price:.2f} per unit while the contracted rate for this period is "
            f"{expected_unit_price:.2f}. That creates a {direction.replace('_', ' ')} variance of {abs(component_variance):.2f}."
        ),
        recommended_action=_rate_action(direction),
        source_clause_text=clause_excerpt,
    )


def _build_quantity_finding(
    contract: Contract,
    invoice: InvoiceLine,
    expected_unit_price: float,
    actual_unit_price: float,
    expected_amount: float,
    clause_excerpt: str | None,
) -> BillingMismatchFinding:
    component_variance = round((invoice.quantity - contract.quantity) * expected_unit_price, 2)
    variance_percent = _variance_percent(invoice.quantity, contract.quantity)
    direction = "underbilled" if component_variance < 0 else "overbilled"
    return BillingMismatchFinding(
        finding_id=f"billing-quantity-{invoice.invoice_id}",
        contract_id=contract.contract_id,
        invoice_id=invoice.invoice_id,
        mismatch_category="quantity",
        mismatch_direction=direction,
        severity=_severity(component_variance, variance_percent),
        billing_period_start=invoice.billing_period_start,
        billing_period_end=invoice.billing_period_end,
        expected_unit_price=expected_unit_price,
        actual_unit_price=actual_unit_price,
        expected_quantity=contract.quantity,
        actual_quantity=invoice.quantity,
        expected_amount=expected_amount,
        actual_amount=invoice.amount_billed,
        variance_amount=component_variance,
        variance_percent=variance_percent,
        explanation=(
            f"Invoice {invoice.invoice_id} billed {invoice.quantity} units while the contract commits {contract.quantity} units. "
            f"That creates a {direction.replace('_', ' ')} quantity variance of {abs(component_variance):.2f} at the contracted rate."
        ),
        recommended_action=_quantity_action(direction),
        source_clause_text=clause_excerpt,
    )


def _build_invoice_review(contract: Contract, invoice: InvoiceLine) -> tuple[BillingInvoiceReview, list[BillingMismatchFinding], str | None]:
    expected_unit_price, clause_excerpt = _expected_unit_price(contract, invoice)
    actual_unit_price = _actual_unit_price(invoice)
    expected_amount = round(expected_unit_price * contract.quantity, 2)
    net_variance_amount = round(invoice.amount_billed - expected_amount, 2)

    findings: list[BillingMismatchFinding] = []
    if abs(actual_unit_price - expected_unit_price) > RATE_TOLERANCE:
        findings.append(
            _build_rate_finding(
                contract=contract,
                invoice=invoice,
                expected_unit_price=expected_unit_price,
                actual_unit_price=actual_unit_price,
                expected_amount=expected_amount,
                clause_excerpt=clause_excerpt,
            )
        )

    if invoice.quantity != contract.quantity:
        findings.append(
            _build_quantity_finding(
                contract=contract,
                invoice=invoice,
                expected_unit_price=expected_unit_price,
                actual_unit_price=actual_unit_price,
                expected_amount=expected_amount,
                clause_excerpt=clause_excerpt,
            )
        )

    review = BillingInvoiceReview(
        invoice_id=invoice.invoice_id,
        billing_period_start=invoice.billing_period_start,
        billing_period_end=invoice.billing_period_end,
        expected_unit_price=expected_unit_price,
        actual_unit_price=actual_unit_price,
        expected_quantity=contract.quantity,
        actual_quantity=invoice.quantity,
        expected_amount=expected_amount,
        actual_amount=invoice.amount_billed,
        net_variance_amount=net_variance_amount,
        status=_invoice_status(net_variance_amount),
    )
    return review, findings, clause_excerpt


def list_billing_mismatch_analyses(as_of: date | None = None) -> list[BillingMismatchAnalysisDetail]:
    effective_date = as_of or date.today()
    accounts_by_id = {account.account_id: account for account in load_accounts()}
    invoices_by_contract = _group_invoices(effective_date)
    details: list[BillingMismatchAnalysisDetail] = []

    for contract in load_contracts():
        invoice_rows = invoices_by_contract.get(contract.contract_id, [])
        invoice_reviews: list[BillingInvoiceReview] = []
        findings: list[BillingMismatchFinding] = []
        governing_clause_excerpt = None
        total_underbilled_amount = 0.0
        total_overbilled_amount = 0.0

        for invoice in invoice_rows:
            review, invoice_findings, clause_excerpt = _build_invoice_review(contract, invoice)
            invoice_reviews.append(review)
            findings.extend(invoice_findings)
            governing_clause_excerpt = governing_clause_excerpt or clause_excerpt
            if review.net_variance_amount < 0:
                total_underbilled_amount += abs(review.net_variance_amount)
            elif review.net_variance_amount > 0:
                total_overbilled_amount += review.net_variance_amount

        latest_review = invoice_reviews[-1] if invoice_reviews else None
        account = accounts_by_id[contract.account_id]
        analysis = BillingMismatchAnalysis(
            analysis_id=f"billing-{contract.contract_id}",
            contract_id=contract.contract_id,
            account_id=contract.account_id,
            account_name=account.name,
            product_name=contract.product_name,
            status="mismatch_detected" if findings else "aligned",
            total_invoices_reviewed=len(invoice_reviews),
            total_findings=len(findings),
            high_severity_count=sum(1 for item in findings if item.severity == "high"),
            total_underbilled_amount=round(total_underbilled_amount, 2),
            total_overbilled_amount=round(total_overbilled_amount, 2),
            latest_billing_period_end=latest_review.billing_period_end if latest_review else None,
            latest_expected_amount=latest_review.expected_amount if latest_review else None,
            latest_actual_amount=latest_review.actual_amount if latest_review else None,
            latest_expected_unit_price=latest_review.expected_unit_price if latest_review else None,
            latest_actual_unit_price=latest_review.actual_unit_price if latest_review else None,
            governing_clause_excerpt=governing_clause_excerpt,
        )
        details.append(
            BillingMismatchAnalysisDetail(
                analysis=analysis,
                invoice_reviews=invoice_reviews,
                findings=findings,
            )
        )

    return sorted(
        details,
        key=lambda item: (
            item.analysis.status != "mismatch_detected",
            -item.analysis.total_underbilled_amount,
            -item.analysis.total_overbilled_amount,
            item.analysis.account_name,
        ),
    )


def get_billing_mismatch_analysis(contract_id: str, as_of: date | None = None) -> BillingMismatchAnalysisDetail | None:
    for detail in list_billing_mismatch_analyses(as_of=as_of):
        if detail.analysis.contract_id == contract_id:
            return detail
    return None


def get_billing_mismatch_dashboard(as_of: date | None = None) -> BillingMismatchDashboard:
    analyses = list_billing_mismatch_analyses(as_of=as_of)
    return BillingMismatchDashboard(
        total_contracts_monitored=len(analyses),
        flagged_contracts=sum(1 for item in analyses if item.analysis.status == "mismatch_detected"),
        total_findings=sum(item.analysis.total_findings for item in analyses),
        high_severity_findings=sum(item.analysis.high_severity_count for item in analyses),
        total_underbilled_amount=round(sum(item.analysis.total_underbilled_amount for item in analyses), 2),
        total_overbilled_amount=round(sum(item.analysis.total_overbilled_amount for item in analyses), 2),
        analyses=analyses,
    )