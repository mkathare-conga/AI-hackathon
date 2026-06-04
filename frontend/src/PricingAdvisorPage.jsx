import React, { useEffect, useState } from "react";

import {
  getPricingDashboard,
  getPricingRecommendation,
} from "./api.js";


const currencyFmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const percentFmt = (value) => `${Math.round((value || 0) * 100)}%`;
const formatCurrency = (value) => currencyFmt.format(value || 0);
const formatDate = (value) => new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });


function PricingDashboardSummary({ dashboard }) {
  if (!dashboard) return null;
  return (
    <div className="pricing-dashboard-summary">
      <div className="pricing-stat pricing-stat--impact">
        <span className="pricing-stat__value">{formatCurrency(dashboard.total_incremental_annual_contract_value)}</span>
        <span className="pricing-stat__label">Incremental ACV</span>
      </div>
      <div className="pricing-stat pricing-stat--accent">
        <span className="pricing-stat__value">{dashboard.opportunities_with_price_uplift}</span>
        <span className="pricing-stat__label">Lift Opportunities</span>
      </div>
      <div className="pricing-stat pricing-stat--neutral">
        <span className="pricing-stat__value">{dashboard.total_opportunities}</span>
        <span className="pricing-stat__label">Deals Scored</span>
      </div>
      <div className="pricing-stat pricing-stat--warning">
        <span className="pricing-stat__value">{percentFmt(dashboard.average_improved_close_confidence)}</span>
        <span className="pricing-stat__label">Avg. Close Confidence</span>
      </div>
    </div>
  );
}


function RecommendationList({ recommendations, selectedId, onSelect }) {
  if (!recommendations || recommendations.length === 0) {
    return <div className="pricing-empty">No pricing opportunities available.</div>;
  }

  return (
    <aside className="pricing-sidebar">
      <h3 className="pricing-sidebar__title">Final-Paper Opportunities</h3>
      <div className="pricing-sidebar__list">
        {recommendations.map((item) => (
          <button
            key={item.recommendation_id}
            className={`pricing-sidebar__item ${selectedId === item.recommendation_id ? "pricing-sidebar__item--active" : ""}`}
            onClick={() => onSelect(item.recommendation_id)}
            type="button"
          >
            <div className="pricing-sidebar__item-header">
              <span className="pricing-sidebar__item-name">{item.account_name}</span>
              <span className={`pricing-badge pricing-badge--${item.recommendation_status === "increase_price" ? "accent" : "neutral"}`}>
                {item.recommendation_status === "increase_price" ? "Lift" : "Hold"}
              </span>
            </div>
            <span className="pricing-sidebar__item-opp">{item.opportunity_name}</span>
            <span className="pricing-sidebar__item-delta">+{formatCurrency(item.incremental_annual_contract_value)} ACV</span>
            <span className="pricing-sidebar__item-meta">{percentFmt(item.improved_price_close_confidence)} close confidence · {item.trained_deal_count} same-company deals</span>
          </button>
        ))}
      </div>
    </aside>
  );
}


function RecommendationDetail({ recommendation, agentDescription }) {
  if (!recommendation) {
    return (
      <div className="pricing-detail pricing-detail--empty">
        <div className="pricing-detail-empty__content">
          <span className="pricing-detail-empty__icon">$</span>
          <h3>Pre-Sign Pricing Advisor</h3>
          <p>{agentDescription}</p>
          <p className="pricing-detail-empty__pitch">"Before we sign, can we hold stronger pricing and still close?"</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pricing-detail">
      <div className="pricing-detail__header">
        <div>
          <h2>{recommendation.account_name}</h2>
          <span className="pricing-detail__opp">{recommendation.opportunity_name} · {recommendation.product_name}</span>
        </div>
        <div className="pricing-detail__header-badges">
          <span className="pricing-badge pricing-badge--neutral">{recommendation.stage.replaceAll("_", " ")}</span>
          <span className={`pricing-badge pricing-badge--${recommendation.recommendation_status === "increase_price" ? "accent" : "neutral"}`}>
            {recommendation.recommendation_status === "increase_price" ? "Increase Price" : "Hold Price"}
          </span>
        </div>
      </div>

      <section className="pricing-section pricing-section--hero">
        <div className="pricing-hero-card">
          <span className="pricing-hero-card__label">Current Unit Price</span>
          <span className="pricing-hero-card__value">{formatCurrency(recommendation.current_unit_price)}</span>
          <span className="pricing-hero-card__sub">{recommendation.current_discount_percent.toFixed(1)}% discount</span>
        </div>
        <div className="pricing-hero-card pricing-hero-card--accent">
          <span className="pricing-hero-card__label">Recommended Unit Price</span>
          <span className="pricing-hero-card__value">{formatCurrency(recommendation.recommended_unit_price)}</span>
          <span className="pricing-hero-card__sub">{recommendation.recommended_discount_percent.toFixed(1)}% discount</span>
        </div>
        <div className="pricing-hero-card">
          <span className="pricing-hero-card__label">Improved Close Confidence</span>
          <span className="pricing-hero-card__value">{percentFmt(recommendation.improved_price_close_confidence)}</span>
          <span className="pricing-hero-card__sub">vs {percentFmt(recommendation.current_close_confidence)} at current price</span>
        </div>
      </section>

      <section className="pricing-section pricing-grid">
        <div className="pricing-panel">
          <h3>Commercial Impact</h3>
          <div className="pricing-metric-row"><span>Current annual value</span><strong>{formatCurrency(recommendation.current_annual_contract_value)}</strong></div>
          <div className="pricing-metric-row"><span>Recommended annual value</span><strong>{formatCurrency(recommendation.recommended_annual_contract_value)}</strong></div>
          <div className="pricing-metric-row pricing-metric-row--accent"><span>Incremental annual value</span><strong>{formatCurrency(recommendation.incremental_annual_contract_value)}</strong></div>
          <div className="pricing-metric-row"><span>Total value at current price</span><strong>{formatCurrency(recommendation.current_total_contract_value)}</strong></div>
          <div className="pricing-metric-row"><span>Total value at improved price</span><strong>{formatCurrency(recommendation.recommended_total_contract_value)}</strong></div>
          <div className="pricing-metric-row pricing-metric-row--accent"><span>Walk-away floor</span><strong>{formatCurrency(recommendation.minimum_floor_unit_price)}</strong></div>
        </div>

        <div className="pricing-panel">
          <h3>Signing Readiness</h3>
          <div className="pricing-metric-row"><span>Approval path</span><strong>{recommendation.approval_path}</strong></div>
          <div className="pricing-metric-row"><span>Same-company win rate</span><strong>{percentFmt(recommendation.same_company_win_rate)}</strong></div>
          <div className="pricing-metric-row"><span>Training deals used</span><strong>{recommendation.trained_deal_count}</strong></div>
          <ul className="pricing-list">
            {recommendation.important_signing_considerations.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </section>

      <section className="pricing-section pricing-grid">
        <div className="pricing-panel">
          <h3>Recommended Actions</h3>
          <ul className="pricing-list">
            {recommendation.recommended_actions.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
        <div className="pricing-panel">
          <h3>Model Highlights</h3>
          <ul className="pricing-list">
            {recommendation.model_highlights.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </section>

      <section className="pricing-section">
        <h3>Closest Same-Company Comparables</h3>
        <div className="pricing-table-wrap">
          <table className="pricing-table">
            <thead>
              <tr>
                <th>Signed</th>
                <th>Outcome</th>
                <th>Unit Price</th>
                <th>Discount</th>
                <th>Qty</th>
                <th>Term</th>
                <th>Support</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {recommendation.comparable_deals.map((deal) => (
                <tr key={deal.deal_id}>
                  <td>{formatDate(deal.signed_date)}</td>
                  <td>
                    <span className={`pricing-badge pricing-badge--${deal.outcome === "won" ? "accent" : "warning"}`}>
                      {deal.outcome}
                    </span>
                  </td>
                  <td>{formatCurrency(deal.final_unit_price)}</td>
                  <td>{deal.discount_percent.toFixed(1)}%</td>
                  <td>{deal.quantity.toLocaleString()}</td>
                  <td>{deal.term_months} mo</td>
                  <td>{deal.support_tier}</td>
                  <td>{deal.notes || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}


export default function PricingAdvisorPage() {
  const [dashboard, setDashboard] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await getPricingDashboard();
        setDashboard(data);
        if (data.recommendations?.length > 0) {
          const firstId = data.recommendations[0].recommendation_id;
          setSelectedId(firstId);
          setSelectedRecommendation(data.recommendations[0]);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  async function handleSelect(recommendationId) {
    setSelectedId(recommendationId);
    try {
      const detail = await getPricingRecommendation(recommendationId);
      setSelectedRecommendation(detail);
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <div className="pricing-page"><div className="loading-page">Loading pricing recommendations…</div></div>;

  return (
    <div className="pricing-page">
      {error && <div className="error-banner">{error}</div>}
      <div className="pricing-page__toolbar">
        <div>
          <h2 className="pricing-page__title">Pre-Sign Pricing Advisor</h2>
          <p className="pricing-page__subtitle">{dashboard?.agent_description}</p>
        </div>
      </div>

      <PricingDashboardSummary dashboard={dashboard} />

      <div className="pricing-layout">
        <RecommendationList
          recommendations={dashboard?.recommendations || []}
          selectedId={selectedId}
          onSelect={handleSelect}
        />
        <main className="pricing-main">
          <RecommendationDetail recommendation={selectedRecommendation} agentDescription={dashboard?.agent_description} />
        </main>
      </div>
    </div>
  );
}