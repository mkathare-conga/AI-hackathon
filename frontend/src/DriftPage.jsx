import React, { useState, useEffect, useCallback } from "react";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function driftRequest(path, options) {
  const response = await fetch(`${BASE_URL}${path}`, options);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function fmt(n) {
  return Number(n || 0).toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function severityColor(severity) {
  return severity === "high" ? "alert" : severity === "medium" ? "warning" : "neutral";
}

function severityLabel(severity) {
  return severity === "high" ? "High" : severity === "medium" ? "Medium" : "Low";
}

function driftTypeLabel(type) {
  const labels = {
    price: "Price Drift",
    quantity: "Quantity Drift",
    scope: "Scope Drift",
    support: "Support Drift",
    payment_terms: "Payment Terms",
    renewal_terms: "Renewal Terms",
  };
  return labels[type] || type;
}

/* ─── Dashboard Summary ───────────────────────────────────────────────────── */

function DriftDashboardSummary({ dashboard }) {
  if (!dashboard) return null;
  return (
    <div className="drift-dashboard-summary">
      <div className="drift-stat drift-stat--alert">
        <span className="drift-stat__value">{dashboard.total_high_severity}</span>
        <span className="drift-stat__label">High Severity</span>
      </div>
      <div className="drift-stat drift-stat--warning">
        <span className="drift-stat__value">{dashboard.total_findings}</span>
        <span className="drift-stat__label">Total Findings</span>
      </div>
      <div className="drift-stat drift-stat--neutral">
        <span className="drift-stat__value">{dashboard.total_quotes_analyzed}</span>
        <span className="drift-stat__label">Quotes Analyzed</span>
      </div>
      <div className="drift-stat drift-stat--impact">
        <span className="drift-stat__value">{fmt(dashboard.total_estimated_impact)}</span>
        <span className="drift-stat__label">Est. Annual Impact</span>
      </div>
    </div>
  );
}

/* ─── Quote List ──────────────────────────────────────────────────────────── */

function QuoteList({ analyses, selectedQuoteId, onSelect }) {
  if (!analyses || analyses.length === 0) {
    return <div className="drift-empty">No drift analyses yet. Click "Run Analysis" to start.</div>;
  }

  return (
    <div className="drift-quote-list">
      {analyses.map((a) => (
        <button
          key={a.quote_id}
          className={`drift-quote-item${selectedQuoteId === a.quote_id ? " drift-quote-item--active" : ""}`}
          onClick={() => onSelect(a)}
          type="button"
        >
          <div className="drift-quote-item__header">
            <span className="drift-quote-item__name">{a.account_name}</span>
            <span className={`drift-badge drift-badge--${severityColor(a.high_severity_count > 0 ? "high" : a.medium_severity_count > 0 ? "medium" : "low")}`}>
              {a.total_findings} finding{a.total_findings !== 1 ? "s" : ""}
            </span>
          </div>
          <span className="drift-quote-item__opp">{a.opportunity_name}</span>
          <span className="drift-quote-item__impact">{fmt(a.total_estimated_annual_impact)} at risk</span>
        </button>
      ))}
    </div>
  );
}

/* ─── Finding Detail Card ─────────────────────────────────────────────────── */

function FindingCard({ finding }) {
  return (
    <div className={`drift-finding-card drift-finding-card--${severityColor(finding.severity)}`}>
      <div className="drift-finding-card__header">
        <span className="drift-finding-card__type">{driftTypeLabel(finding.drift_type)}</span>
        <span className={`drift-badge drift-badge--${severityColor(finding.severity)}`}>
          {severityLabel(finding.severity)}
        </span>
      </div>
      <div className="drift-finding-card__comparison">
        <div className="drift-finding-card__side">
          <span className="drift-finding-card__label">Quote</span>
          <span className="drift-finding-card__value">{finding.quote_value}</span>
        </div>
        <span className="drift-finding-card__arrow">→</span>
        <div className="drift-finding-card__side">
          <span className="drift-finding-card__label">Contract</span>
          <span className="drift-finding-card__value drift-finding-card__value--changed">{finding.contract_value}</span>
        </div>
      </div>
      <p className="drift-finding-card__explanation">{finding.explanation}</p>
      {finding.estimated_annual_impact > 0 && (
        <div className="drift-finding-card__impact">
          Impact: {fmt(finding.estimated_annual_impact)}/year
        </div>
      )}
      {finding.source_clause_text && (
        <blockquote className="drift-finding-card__clause">{finding.source_clause_text}</blockquote>
      )}
    </div>
  );
}

/* ─── Analysis Detail Panel ───────────────────────────────────────────────── */

function AnalysisDetail({ analysis, quoteLines }) {
  if (!analysis) {
    return (
      <div className="drift-detail-empty">
        <div className="drift-detail-empty__content">
          <span className="drift-detail-empty__icon">⇄</span>
          <h3>Quote-to-Contract Drift Detector</h3>
          <p>
            Compares what sales approved in the quote with what legal ultimately signed.
            Highlights changes that materially affect price, scope, support, renewal rights, or payment terms.
          </p>
          <p className="drift-detail-empty__pitch">
            "Did we actually sign what we sold?"
          </p>
        </div>
      </div>
    );
  }

  const findingsByType = {};
  for (const f of analysis.findings) {
    if (!findingsByType[f.drift_type]) findingsByType[f.drift_type] = [];
    findingsByType[f.drift_type].push(f);
  }

  return (
    <div className="drift-detail">
      <div className="drift-detail__header">
        <div>
          <h2>{analysis.account_name}</h2>
          <span className="drift-detail__opp">{analysis.opportunity_name}</span>
        </div>
        <div className="drift-detail__stats">
          <span className={`drift-badge drift-badge--${analysis.high_severity_count > 0 ? "alert" : "neutral"}`}>
            {analysis.high_severity_count} High
          </span>
          <span className="drift-badge drift-badge--warning">{analysis.medium_severity_count} Med</span>
          <span className="drift-detail__total-impact">{fmt(analysis.total_estimated_annual_impact)}</span>
        </div>
      </div>

      {quoteLines && quoteLines.length > 0 && (
        <section className="drift-section">
          <h3>Quoted Line Items</h3>
          <div className="drift-table-wrap">
            <table className="drift-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Qty</th>
                  <th>Unit Price</th>
                  <th>Discount</th>
                  <th>Support</th>
                  <th>Uplift</th>
                  <th>Payment</th>
                </tr>
              </thead>
              <tbody>
                {quoteLines.map((line) => (
                  <tr key={line.line_id}>
                    <td>{line.product_name}</td>
                    <td>{line.quantity.toLocaleString()}</td>
                    <td>${line.unit_price.toFixed(2)}</td>
                    <td>{line.discount_percent}%</td>
                    <td>{line.support_tier}</td>
                    <td>{line.renewal_uplift_percent != null ? `${line.renewal_uplift_percent}%` : "—"}</td>
                    <td>Net {line.payment_terms_days}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="drift-section">
        <h3>Drift Findings ({analysis.total_findings})</h3>
        {Object.entries(findingsByType).map(([type, findings]) => (
          <div key={type} className="drift-finding-group">
            <h4 className="drift-finding-group__title">{driftTypeLabel(type)} ({findings.length})</h4>
            {findings.map((f) => <FindingCard key={f.finding_id} finding={f} />)}
          </div>
        ))}
        {analysis.findings.length === 0 && (
          <p className="drift-empty">No drift detected — contract matches the quote.</p>
        )}
      </section>
    </div>
  );
}

/* ─── Main Drift Page ─────────────────────────────────────────────────────── */

export default function DriftPage() {
  const [dashboard, setDashboard] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [quoteLines, setQuoteLines] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    try {
      const data = await driftRequest("/api/drift/dashboard");
      setDashboard(data);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  async function handleSelect(analysis) {
    setSelectedAnalysis(analysis);
    try {
      const lines = await driftRequest(`/api/drift/quotes/${analysis.quote_id}/lines`);
      setQuoteLines(lines);
    } catch (err) {
      setQuoteLines([]);
    }
  }

  async function handleAnalyzeAll() {
    setAnalyzing(true);
    setError("");
    try {
      const result = await driftRequest("/api/drift/analyze-all", { method: "POST" });
      setDashboard(result);
      if (result.analyses.length > 0 && !selectedAnalysis) {
        handleSelect(result.analyses[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="drift-page">
      <div className="drift-page__toolbar">
        <h2 className="drift-page__title">Quote-to-Contract Drift Detector</h2>
        <button
          className="drift-analyze-btn"
          onClick={handleAnalyzeAll}
          disabled={analyzing}
        >
          {analyzing ? "Analyzing…" : "Run Analysis"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <DriftDashboardSummary dashboard={dashboard} />

      <div className="drift-layout">
        <aside className="drift-sidebar">
          <QuoteList
            analyses={dashboard?.analyses || []}
            selectedQuoteId={selectedAnalysis?.quote_id}
            onSelect={handleSelect}
          />
        </aside>
        <main className="drift-main">
          <AnalysisDetail analysis={selectedAnalysis} quoteLines={quoteLines} />
        </main>
      </div>
    </div>
  );
}
