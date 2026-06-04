import React, { useEffect, useState } from "react";

import { getBillingMismatchDashboard } from "./api.js";


const currencyFmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const numberFmt = new Intl.NumberFormat("en-US");

const formatCurrency = (value) => currencyFmt.format(value || 0);
const formatUnitPrice = (value) => `${currencyFmt.format(value || 0)} / unit`;
const formatDate = (value) => new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
const formatSignedCurrency = (value) => `${value >= 0 ? "+" : "-"}${formatCurrency(Math.abs(value))}`;

const STATUS_LABELS = {
  mismatch_detected: "Mismatch detected",
  aligned: "Aligned",
  underbilled: "Underbilled",
  overbilled: "Overbilled",
};


function DashboardSummary({ dashboard }) {
  if (!dashboard) return null;

  return (
    <div className="billing-dashboard-summary">
      <div className="billing-stat billing-stat--neutral">
        <span className="billing-stat__value">{dashboard.total_contracts_monitored}</span>
        <span className="billing-stat__label">Contracts Monitored</span>
      </div>
      <div className="billing-stat billing-stat--warning">
        <span className="billing-stat__value">{dashboard.flagged_contracts}</span>
        <span className="billing-stat__label">Flagged Contracts</span>
      </div>
      <div className="billing-stat billing-stat--alert">
        <span className="billing-stat__value">{dashboard.total_findings}</span>
        <span className="billing-stat__label">Findings</span>
      </div>
      <div className="billing-stat billing-stat--under">
        <span className="billing-stat__value">{formatCurrency(dashboard.total_underbilled_amount)}</span>
        <span className="billing-stat__label">Underbilled</span>
      </div>
      <div className="billing-stat billing-stat--over">
        <span className="billing-stat__value">{formatCurrency(dashboard.total_overbilled_amount)}</span>
        <span className="billing-stat__label">Overbilled</span>
      </div>
    </div>
  );
}


function AnalysisList({ analyses, selectedId, onSelect }) {
  return (
    <aside className="billing-sidebar">
      <h3 className="billing-sidebar__title">Billing Health By Contract</h3>
      <div className="billing-sidebar__list">
        {analyses.map((detail) => {
          const analysis = detail.analysis;
          const amountText = analysis.total_underbilled_amount > 0
            ? `${formatCurrency(analysis.total_underbilled_amount)} underbilled`
            : analysis.total_overbilled_amount > 0
              ? `${formatCurrency(analysis.total_overbilled_amount)} overbilled`
              : "No mismatch detected";
          return (
            <button
              key={analysis.analysis_id}
              className={`billing-sidebar__item ${selectedId === analysis.analysis_id ? "billing-sidebar__item--active" : ""}`}
              onClick={() => onSelect(detail)}
              type="button"
            >
              <div className="billing-sidebar__item-header">
                <span className="billing-sidebar__item-name">{analysis.account_name}</span>
                <span className={`billing-badge billing-badge--${analysis.status === "mismatch_detected" ? "mismatch" : "aligned"}`}>
                  {STATUS_LABELS[analysis.status]}
                </span>
              </div>
              <span className="billing-sidebar__item-product">{analysis.product_name}</span>
              <span className="billing-sidebar__item-meta">{analysis.total_findings} findings · {analysis.total_invoices_reviewed} invoices reviewed</span>
              <span className={`billing-sidebar__item-amount ${analysis.total_underbilled_amount > 0 ? "billing-sidebar__item-amount--under" : analysis.total_overbilled_amount > 0 ? "billing-sidebar__item-amount--over" : ""}`}>
                {amountText}
              </span>
            </button>
          );
        })}
      </div>
    </aside>
  );
}


function InvoiceReviewTable({ invoiceReviews }) {
  return (
    <div className="billing-table-wrap">
      <table className="billing-table">
        <thead>
          <tr>
            <th>Period</th>
            <th>Status</th>
            <th>Expected Rate</th>
            <th>Actual Rate</th>
            <th>Expected Qty</th>
            <th>Actual Qty</th>
            <th>Expected Amount</th>
            <th>Actual Amount</th>
            <th>Net Variance</th>
          </tr>
        </thead>
        <tbody>
          {invoiceReviews.map((review) => (
            <tr key={review.invoice_id}>
              <td>{formatDate(review.billing_period_start)} - {formatDate(review.billing_period_end)}</td>
              <td>
                <span className={`billing-badge billing-badge--${review.status}`}>
                  {STATUS_LABELS[review.status]}
                </span>
              </td>
              <td>{formatUnitPrice(review.expected_unit_price)}</td>
              <td>{formatUnitPrice(review.actual_unit_price)}</td>
              <td>{numberFmt.format(review.expected_quantity)}</td>
              <td>{numberFmt.format(review.actual_quantity)}</td>
              <td>{formatCurrency(review.expected_amount)}</td>
              <td>{formatCurrency(review.actual_amount)}</td>
              <td className={review.net_variance_amount < 0 ? "billing-table__variance billing-table__variance--under" : review.net_variance_amount > 0 ? "billing-table__variance billing-table__variance--over" : "billing-table__variance"}>
                {formatSignedCurrency(review.net_variance_amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function FindingCard({ finding }) {
  const findingLabel = `${finding.mismatch_category === "rate" ? "Rate" : "Quantity"} ${finding.mismatch_direction}`;

  return (
    <div className={`billing-finding-card billing-finding-card--${finding.mismatch_direction}`}>
      <div className="billing-finding-card__header">
        <div>
          <span className="billing-finding-card__title">{findingLabel}</span>
          <span className="billing-finding-card__period">{formatDate(finding.billing_period_start)} - {formatDate(finding.billing_period_end)}</span>
        </div>
        <div className="billing-finding-card__badges">
          <span className={`billing-badge billing-badge--${finding.mismatch_direction}`}>{STATUS_LABELS[finding.mismatch_direction]}</span>
          <span className={`billing-badge billing-badge--${finding.severity}`}>{finding.severity}</span>
        </div>
      </div>
      <div className="billing-finding-card__metrics">
        <div>
          <span className="billing-finding-card__label">Expected</span>
          <strong>{finding.mismatch_category === "rate" ? formatUnitPrice(finding.expected_unit_price) : `${numberFmt.format(finding.expected_quantity)} units`}</strong>
        </div>
        <div>
          <span className="billing-finding-card__label">Actual</span>
          <strong>{finding.mismatch_category === "rate" ? formatUnitPrice(finding.actual_unit_price) : `${numberFmt.format(finding.actual_quantity)} units`}</strong>
        </div>
        <div>
          <span className="billing-finding-card__label">Variance</span>
          <strong>{formatSignedCurrency(finding.variance_amount)}</strong>
        </div>
      </div>
      <p className="billing-finding-card__explanation">{finding.explanation}</p>
      <p className="billing-finding-card__action"><strong>Action:</strong> {finding.recommended_action}</p>
      {finding.source_clause_text && <blockquote className="billing-finding-card__clause">{finding.source_clause_text}</blockquote>}
    </div>
  );
}


function AnalysisDetail({ detail }) {
  if (!detail) {
    return (
      <div className="billing-detail billing-detail--empty">
        <div className="billing-detail-empty__content">
          <span className="billing-detail-empty__icon">≠</span>
          <h3>Billing vs Contract Mismatch</h3>
          <p>
            Cross-references invoiced rates and quantities against the controlling contract terms.
            It surfaces underbilling, overbilling, and invoice drift after amendments or renewal uplifts take effect.
          </p>
          <p className="billing-detail-empty__pitch">"Are we billing exactly what the contract says we should bill?"</p>
        </div>
      </div>
    );
  }

  const analysis = detail.analysis;

  return (
    <div className="billing-detail">
      <div className="billing-detail__header">
        <div>
          <h2>{analysis.account_name}</h2>
          <span className="billing-detail__product">{analysis.product_name}</span>
        </div>
        <div className="billing-detail__badges">
          <span className={`billing-badge billing-badge--${analysis.status === "mismatch_detected" ? "mismatch" : "aligned"}`}>
            {STATUS_LABELS[analysis.status]}
          </span>
          <span className="billing-badge billing-badge--neutral">{analysis.total_findings} findings</span>
        </div>
      </div>

      <section className="billing-hero-grid">
        <div className="billing-card">
          <span className="billing-card__label">Latest Expected Bill</span>
          <span className="billing-card__value">{formatCurrency(analysis.latest_expected_amount)}</span>
          <span className="billing-card__sub">{analysis.latest_expected_unit_price != null ? formatUnitPrice(analysis.latest_expected_unit_price) : "No invoices yet"}</span>
        </div>
        <div className="billing-card">
          <span className="billing-card__label">Latest Actual Bill</span>
          <span className="billing-card__value">{formatCurrency(analysis.latest_actual_amount)}</span>
          <span className="billing-card__sub">{analysis.latest_actual_unit_price != null ? formatUnitPrice(analysis.latest_actual_unit_price) : "No invoices yet"}</span>
        </div>
        <div className="billing-card billing-card--under">
          <span className="billing-card__label">Underbilled</span>
          <span className="billing-card__value">{formatCurrency(analysis.total_underbilled_amount)}</span>
          <span className="billing-card__sub">Captured across {analysis.total_invoices_reviewed} invoices</span>
        </div>
        <div className="billing-card billing-card--over">
          <span className="billing-card__label">Overbilled</span>
          <span className="billing-card__value">{formatCurrency(analysis.total_overbilled_amount)}</span>
          <span className="billing-card__sub">{analysis.high_severity_count} high severity findings</span>
        </div>
      </section>

      <section className="billing-section">
        <h3>Invoice Reviews</h3>
        <InvoiceReviewTable invoiceReviews={detail.invoice_reviews} />
      </section>

      {analysis.governing_clause_excerpt && (
        <section className="billing-section">
          <h3>Controlling Contract Clause</h3>
          <blockquote className="billing-quote">{analysis.governing_clause_excerpt}</blockquote>
        </section>
      )}

      <section className="billing-section">
        <h3>Findings</h3>
        {detail.findings.length === 0 ? (
          <div className="billing-empty">Invoices match the contracted rate and quantity for the periods reviewed.</div>
        ) : (
          <div className="billing-findings">
            {detail.findings.map((finding) => <FindingCard key={finding.finding_id} finding={finding} />)}
          </div>
        )}
      </section>
    </div>
  );
}


export default function BillingMismatchPage() {
  const [dashboard, setDashboard] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await getBillingMismatchDashboard();
        setDashboard(data);
        if (data.analyses?.length > 0) {
          setSelectedId(data.analyses[0].analysis.analysis_id);
          setSelectedDetail(data.analyses[0]);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  function handleSelect(detail) {
    setSelectedId(detail.analysis.analysis_id);
    setSelectedDetail(detail);
  }

  if (loading) return <div className="billing-page"><div className="loading-page">Loading billing mismatches…</div></div>;

  return (
    <div className="billing-page">
      {error && <div className="error-banner">{error}</div>}
      <div className="billing-page__toolbar">
        <div>
          <h2 className="billing-page__title">Billing vs Contract Mismatch</h2>
          <p className="billing-page__subtitle">
            Cross-reference every billed line against the controlling contract rate and committed quantity to spot underbilling, overbilling, and renewal pricing drift.
          </p>
        </div>
      </div>

      <DashboardSummary dashboard={dashboard} />

      <div className="billing-layout">
        <AnalysisList analyses={dashboard?.analyses || []} selectedId={selectedId} onSelect={handleSelect} />
        <main className="billing-main">
          <AnalysisDetail detail={selectedDetail} />
        </main>
      </div>
    </div>
  );
}