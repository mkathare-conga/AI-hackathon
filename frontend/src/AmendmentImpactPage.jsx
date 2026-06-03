import React, { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL || "";

const currencyFmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const formatCurrency = (v) => currencyFmt.format(v || 0);
const formatDate = (v) => new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

const SEVERITY_COLORS = { high: "#e74c3c", medium: "#f39c12", low: "#27ae60" };
const PRIORITY_LABELS = { urgent: "🔴 Urgent", high: "🟠 High", medium: "🟡 Medium", low: "🟢 Low" };

/* ─── Dashboard Summary ───────────────────────────────────────────────────── */

function DashboardSummary({ dashboard }) {
  if (!dashboard) return null;
  return (
    <div className="amendment-dashboard-summary">
      <div className="amendment-stat">
        <span className="amendment-stat__value">{dashboard.total_analyses}</span>
        <span className="amendment-stat__label">Amendments Analyzed</span>
      </div>
      <div className="amendment-stat">
        <span className="amendment-stat__value">{dashboard.total_impacts}</span>
        <span className="amendment-stat__label">Changes Detected</span>
      </div>
      <div className={`amendment-stat ${dashboard.net_annual_revenue_delta >= 0 ? "amendment-stat--positive" : "amendment-stat--negative"}`}>
        <span className="amendment-stat__value">{formatCurrency(dashboard.net_annual_revenue_delta)}</span>
        <span className="amendment-stat__label">Net Revenue Impact</span>
      </div>
      <div className="amendment-stat">
        <span className="amendment-stat__value">{dashboard.total_action_items_open}</span>
        <span className="amendment-stat__label">Open Actions</span>
      </div>
      <div className="amendment-stat amendment-stat--positive">
        <span className="amendment-stat__value">{dashboard.positive_amendments}</span>
        <span className="amendment-stat__label">Positive</span>
      </div>
      <div className="amendment-stat amendment-stat--negative">
        <span className="amendment-stat__value">{dashboard.negative_amendments}</span>
        <span className="amendment-stat__label">Negative</span>
      </div>
    </div>
  );
}

/* ─── Analysis List (Sidebar) ─────────────────────────────────────────────── */

function AnalysisList({ analyses, selectedId, onSelect }) {
  return (
    <aside className="amendment-sidebar">
      <h3 className="amendment-sidebar__title">Amendment Analyses</h3>
      <div className="amendment-sidebar__list">
        {analyses.map((detail) => {
          const a = detail.analysis;
          const isPositive = a.total_annual_revenue_delta >= 0;
          return (
            <button
              key={a.analysis_id}
              className={`amendment-sidebar__item ${selectedId === a.analysis_id ? "amendment-sidebar__item--active" : ""}`}
              onClick={() => onSelect(a.analysis_id)}
              type="button"
            >
              <div className="amendment-sidebar__item-header">
                <span className="amendment-sidebar__item-name">{a.account_name}</span>
                <span className={`amendment-sidebar__item-delta ${isPositive ? "positive" : "negative"}`}>
                  {isPositive ? "+" : ""}{formatCurrency(a.total_annual_revenue_delta)}
                </span>
              </div>
              <div className="amendment-sidebar__item-meta">
                <span>{formatDate(a.amendment_date)}</span>
                <span>{a.total_changes} changes • {a.high_impact_count} high</span>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

/* ─── Impact Card ─────────────────────────────────────────────────────────── */

function ImpactCard({ impact }) {
  return (
    <div className="amendment-impact-card">
      <div className="amendment-impact-card__header">
        <span
          className="amendment-impact-card__severity"
          style={{ background: SEVERITY_COLORS[impact.severity] }}
        >
          {impact.severity.toUpperCase()}
        </span>
        <span className="amendment-impact-card__category">
          {impact.impact_category.replace(/_/g, " ")}
        </span>
        {impact.annual_revenue_delta != null && impact.annual_revenue_delta !== 0 && (
          <span className={`amendment-impact-card__delta ${impact.annual_revenue_delta >= 0 ? "positive" : "negative"}`}>
            {impact.annual_revenue_delta >= 0 ? "+" : ""}{formatCurrency(impact.annual_revenue_delta)}/yr
          </span>
        )}
      </div>
      <div className="amendment-impact-card__change">
        <div className="amendment-impact-card__before">
          <span className="label">Before:</span> {impact.before_value}
        </div>
        <div className="amendment-impact-card__arrow">→</div>
        <div className="amendment-impact-card__after">
          <span className="label">After:</span> {impact.after_value}
        </div>
      </div>
      <p className="amendment-impact-card__explanation">{impact.explanation}</p>
      {impact.source_clause_text && (
        <blockquote className="amendment-impact-card__clause">"{impact.source_clause_text}"</blockquote>
      )}
      <div className="amendment-impact-card__flags">
        {impact.requires_billing_update && <span className="flag flag--billing">Billing Update</span>}
        {impact.requires_workflow_update && <span className="flag flag--workflow">Workflow Update</span>}
        <span className="flag flag--confidence">Confidence: {Math.round(impact.confidence_score * 100)}%</span>
      </div>
    </div>
  );
}

/* ─── Action Item Row ─────────────────────────────────────────────────────── */

function ActionItemRow({ action, onStatusChange }) {
  return (
    <div className={`amendment-action-row amendment-action-row--${action.status}`}>
      <div className="amendment-action-row__left">
        <span className="amendment-action-row__priority">{PRIORITY_LABELS[action.priority] || action.priority}</span>
        <span className="amendment-action-row__desc">{action.description}</span>
      </div>
      <div className="amendment-action-row__right">
        <span className="amendment-action-row__team">{action.assigned_team || "Unassigned"}</span>
        <select
          className="amendment-action-row__status-select"
          value={action.status}
          onChange={(e) => onStatusChange(action.action_id, e.target.value)}
        >
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="dismissed">Dismissed</option>
        </select>
      </div>
    </div>
  );
}

/* ─── Analysis Detail Panel ───────────────────────────────────────────────── */

function AnalysisDetail({ detail, onActionStatusChange }) {
  if (!detail) return <div className="amendment-detail-empty">Select an amendment analysis to view details</div>;

  const { analysis, impacts, action_items } = detail;

  return (
    <div className="amendment-detail">
      <div className="amendment-detail__header">
        <h2>{analysis.account_name}</h2>
        <span className="amendment-detail__date">{formatDate(analysis.amendment_date)}</span>
        <span className={`amendment-detail__delta ${analysis.total_annual_revenue_delta >= 0 ? "positive" : "negative"}`}>
          {analysis.total_annual_revenue_delta >= 0 ? "+" : ""}{formatCurrency(analysis.total_annual_revenue_delta)}/yr
        </span>
      </div>
      <p className="amendment-detail__summary">{analysis.amendment_summary}</p>

      <h3 className="amendment-detail__section-title">Impacts ({impacts.length})</h3>
      <div className="amendment-detail__impacts">
        {impacts.map((impact) => <ImpactCard key={impact.impact_id} impact={impact} />)}
      </div>

      <h3 className="amendment-detail__section-title">Action Items ({action_items.length})</h3>
      <div className="amendment-detail__actions">
        {action_items.map((action) => (
          <ActionItemRow key={action.action_id} action={action} onStatusChange={onActionStatusChange} />
        ))}
      </div>
    </div>
  );
}

/* ─── Main Page ───────────────────────────────────────────────────────────── */

export default function AmendmentImpactPage() {
  const [dashboard, setDashboard] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API}/api/amendments/dashboard`);
      if (!resp.ok) throw new Error("Failed to load amendment dashboard");
      const data = await resp.json();
      setDashboard(data);
      // Auto-select first analysis
      if (data.analyses?.length > 0 && !selectedId) {
        const firstId = data.analyses[0].analysis.analysis_id;
        setSelectedId(firstId);
        setSelectedDetail(data.analyses[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSelect(analysisId) {
    setSelectedId(analysisId);
    const detail = dashboard?.analyses?.find((d) => d.analysis.analysis_id === analysisId);
    setSelectedDetail(detail || null);
  }

  async function handleActionStatusChange(actionId, newStatus) {
    try {
      const resp = await fetch(`${API}/api/amendments/actions/${actionId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!resp.ok) throw new Error("Failed to update action status");
      // Refresh dashboard to get updated data
      await loadDashboard();
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <div className="amendment-page"><div className="loading-page">Loading amendment data…</div></div>;
  if (error) return <div className="amendment-page"><div className="error-banner">{error}</div></div>;

  return (
    <div className="amendment-page">
      <DashboardSummary dashboard={dashboard} />
      <div className="amendment-layout">
        <AnalysisList
          analyses={dashboard?.analyses || []}
          selectedId={selectedId}
          onSelect={handleSelect}
        />
        <AnalysisDetail
          detail={selectedDetail}
          onActionStatusChange={handleActionStatusChange}
        />
      </div>
    </div>
  );
}
