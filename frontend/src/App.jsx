import React, { useEffect, useState } from "react";
import SetupPage from "./SetupPage.jsx";
import DriftPage from "./DriftPage.jsx";
import AmendmentImpactPage from "./AmendmentImpactPage.jsx";

import {
  getContractAIBrief,
  getAIStatus,
  getAccounts,
  getCase,
  getCases,
  getContractFacts,
  getDashboardSummary,
  getDocumentContentUrl,
  importContractDocument,
  getPrediction,
  getPredictions,
} from "./api.js";

const DOCUMENT_TYPE_OPTIONS = [
  { value: "amendment", label: "Amendment" },
  { value: "msa", label: "Master agreement" },
  { value: "nda", label: "NDA" },
  { value: "order_form", label: "Order form" },
  { value: "renewal_notice", label: "Renewal notice" },
];

const AGENT_ROSTER = [
  { id: "revenue-leakage", name: "Revenue Leakage Investigator", status: "Live", isActive: true, description: "Finds missed uplifts and renewal failures by resolving governing terms across contract documents." },
  { id: "quote-drift", name: "Quote-to-Contract Drift Detector", status: "Live", isActive: true, description: "Compares quoted terms to signed contract terms to catch negotiation drift." },
  { id: "amendment-impact", name: "Amendment Impact Detector", status: "Live", isActive: true, description: "Identifies downstream billing or obligation changes triggered by new amendments." },
  { id: "billing-mismatch", name: "Billing vs Contract Mismatch", status: "Planned", isActive: false, description: "Cross-references live billing feeds against contracted rates and quantities." },
];

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function formatCurrency(value) {
  return currencyFormatter.format(value || 0);
}

function formatDate(value) {
  return new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function labelDocumentType(value) {
  const labels = { amendment: "Amendment", msa: "Master agreement", nda: "NDA", order_form: "Order form", renewal_notice: "Renewal notice" };
  return labels[value] || value;
}

function labelExtractionMethod(value) {
  const labels = {
    "ai-resolved-commercial-terms": "AI multi-document term resolution",
    "rule-resolved-commercial-terms": "Rule-based dossier resolution",
    "ai-model": "AI contract-text extraction",
    "ai-pdf-native-text": "AI document extraction",
    "ai-docx-native-text": "AI document extraction",
    "regex-contract-text": "Regex contract fallback",
    "pdf-native-text": "Regex document fallback",
    "docx-native-text": "Regex document fallback",
  };
  if (!value) return "Unknown";
  return labels[value] || value.replaceAll("-", " ");
}

function formatConfidence(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function sameObligationTerms(left, right) {
  if (!left || !right) return false;
  return left.value === right.value && left.notice_window_days === right.notice_window_days && left.effective_date === right.effective_date;
}

/* ─── Account Sidebar ─────────────────────────────────────────────────────── */

function AccountSidebar({ summary, cases, predictions, accounts, selectedId, onSelectCase, onSelectPrediction, onSelectAccount }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <h2>Accounts</h2>
      </div>

      <div className="sidebar__summary">
        <div className="sidebar__stat sidebar__stat--alert">
          <span className="sidebar__stat-value">{formatCurrency(summary?.total_estimated_missed_revenue)}</span>
          <span className="sidebar__stat-label">Missed</span>
        </div>
        <div className="sidebar__stat sidebar__stat--warning">
          <span className="sidebar__stat-value">{formatCurrency(summary?.total_predicted_at_risk_revenue)}</span>
          <span className="sidebar__stat-label">At risk</span>
        </div>
        <div className="sidebar__stat sidebar__stat--neutral">
          <span className="sidebar__stat-value">{summary?.flagged_accounts ?? 0}</span>
          <span className="sidebar__stat-label">Flagged</span>
        </div>
      </div>

      <div className="sidebar__section-label">Leakage Cases</div>
      <div className="sidebar__list">
        {cases.map((item) => (
          <button
            key={item.case_id}
            className={`sidebar__item ${selectedId === item.case_id ? "sidebar__item--active" : ""}`}
            onClick={() => onSelectCase(item)}
            type="button"
          >
            <span className="sidebar__item-indicator sidebar__item-indicator--alert">●</span>
            <div className="sidebar__item-content">
              <span className="sidebar__item-name">{item.account_name}</span>
              <span className="sidebar__item-amount">{formatCurrency(item.estimated_impact)}</span>
              <span className="sidebar__item-type">Missed uplift</span>
            </div>
          </button>
        ))}
      </div>

      <div className="sidebar__section-label">At-Risk Predictions</div>
      <div className="sidebar__list">
        {predictions.map((item) => (
          <button
            key={item.prediction_id}
            className={`sidebar__item ${selectedId === item.prediction_id ? "sidebar__item--active" : ""}`}
            onClick={() => onSelectPrediction(item)}
            type="button"
          >
            <span className="sidebar__item-indicator sidebar__item-indicator--warning">⚠</span>
            <div className="sidebar__item-content">
              <span className="sidebar__item-name">{item.account_name}</span>
              <span className="sidebar__item-amount">{formatCurrency(item.predicted_impact)} at risk</span>
              <span className="sidebar__item-type">{item.days_until_deadline}d until deadline</span>
            </div>
          </button>
        ))}
      </div>

      {(() => {
        const caseAccountIds = new Set(cases.map(c => c.account_id));
        const predAccountIds = new Set(predictions.map(p => p.account_id));
        const others = accounts.filter(a => !caseAccountIds.has(a.account_id) && !predAccountIds.has(a.account_id) && a.primary_contract_id);
        if (others.length === 0) return null;
        return (
          <>
            <div className="sidebar__section-label">All Accounts</div>
            <div className="sidebar__list">
              {others.map((item) => (
                <button
                  key={item.account_id}
                  className={`sidebar__item ${selectedId === item.account_id ? "sidebar__item--active" : ""}`}
                  onClick={() => onSelectAccount(item)}
                  type="button"
                >
                  <span className="sidebar__item-indicator sidebar__item-indicator--neutral">○</span>
                  <div className="sidebar__item-content">
                    <span className="sidebar__item-name">{item.name}</span>
                    <span className="sidebar__item-amount">{item.contract_count} contract{item.contract_count !== 1 ? "s" : ""}</span>
                    <span className="sidebar__item-type">No analysis yet</span>
                  </div>
                </button>
              ))}
            </div>
          </>
        );
      })()}

      <div className="sidebar__section-label">Platform Agent Roster</div>
      <div className="sidebar__roster">
        {AGENT_ROSTER.map((agent) => (
          <div key={agent.id} className={`roster__item ${agent.isActive ? "roster__item--active" : "roster__item--planned"}`}>
            <div className="roster__item-header">
              <span className="roster__item-name">{agent.name}</span>
              <span className={`roster__item-status ${agent.isActive ? "roster__item-status--live" : "roster__item-status--planned"}`}>
                {agent.status}
              </span>
            </div>
            <span className="roster__item-desc">{agent.description}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}

/* ─── Finding Summary ─────────────────────────────────────────────────────── */

function FindingSummary({ selectedType, detail, obligation }) {
  if (!detail) return null;

  const impact = selectedType === "case" ? detail.estimated_impact : detail.predicted_impact;
  const explanation = selectedType === "case" ? detail.explanation : detail.recommended_action;

  return (
    <section className="detail-card detail-card--finding">
      <div className="detail-card__header">
        <h3>Finding</h3>
        <span className={`badge badge--${selectedType === "case" ? "alert" : "warning"}`}>
          {selectedType === "case" ? "Missed uplift" : "At risk"}
        </span>
      </div>
      <div className="finding__impact">{formatCurrency(impact)}</div>
      <p className="finding__explanation">{explanation}</p>
      {obligation && (
        <div className="finding__obligation">
          <span className="finding__term">{obligation.value}% annual uplift</span>
          <span className="finding__meta">
            Effective {formatDate(obligation.effective_date)} · {obligation.notice_window_days}d notice
          </span>
        </div>
      )}
      <div className="finding__action">
        <strong>Action:</strong> {detail.recommended_action}
      </div>
    </section>
  );
}

/* ─── Document Conflict Resolution ────────────────────────────────────────── */

function DocumentConflicts({ obligation, candidateObligations, documents }) {
  if (!obligation || !candidateObligations || candidateObligations.length === 0) return null;

  const documentMap = new Map(documents.map((d) => [d.document_id, d]));
  const controlling = [];
  const superseded = [];
  const seen = new Set();

  for (const candidate of candidateObligations) {
    const key = `${candidate.document_id}::${candidate.source_clause_text}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const isControlling = sameObligationTerms(candidate, obligation) && candidate.document_id === obligation.document_id;
    const doc = documentMap.get(candidate.document_id);
    if (isControlling) controlling.push({ candidate, doc });
    else superseded.push({ candidate, doc });
  }

  return (
    <section className="detail-card detail-card--conflicts">
      <div className="detail-card__header">
        <h3>Document Conflict Resolution</h3>
        <span className="badge badge--neutral">
          {candidateObligations.length} doc{candidateObligations.length === 1 ? "" : "s"} · {superseded.length} conflicting
        </span>
      </div>

      {controlling.length > 0 && (
        <div className="conflict__group">
          <div className="conflict__group-label conflict__group-label--controlling">✓ CONTROLLING</div>
          {controlling.map(({ candidate, doc }) => (
            <div className="conflict__card conflict__card--controlling" key={`ctrl-${candidate.document_id}`}>
              <div className="conflict__card-header">
                <strong>{doc?.file_name || "Contract record"}</strong>
                <span className="conflict__confidence">{formatConfidence(candidate.confidence_score)} confidence</span>
              </div>
              <div className="conflict__card-meta">
                {doc ? `${labelDocumentType(doc.document_type)} · v${doc.version}` : "Base contract"} · {candidate.value}% uplift · {candidate.notice_window_days}d notice
              </div>
              <blockquote className="conflict__quote">{candidate.source_clause_text}</blockquote>
            </div>
          ))}
        </div>
      )}

      {superseded.length > 0 && (
        <div className="conflict__group">
          <div className="conflict__group-label conflict__group-label--superseded">✗ SUPERSEDED ({superseded.length})</div>
          {superseded.map(({ candidate, doc }) => (
            <div className="conflict__card conflict__card--superseded" key={`sup-${candidate.document_id}-${candidate.value}`}>
              <div className="conflict__card-header">
                <strong>{doc?.file_name || "Contract record"}</strong>
                <span className="conflict__confidence">{formatConfidence(candidate.confidence_score)}</span>
              </div>
              <div className="conflict__card-meta">
                {doc ? `${labelDocumentType(doc.document_type)} · v${doc.version}` : "Base"} · {candidate.value}% uplift · {candidate.notice_window_days}d notice
              </div>
              <blockquote className="conflict__quote">{candidate.source_clause_text}</blockquote>
            </div>
          ))}
        </div>
      )}

      {controlling.length > 0 && (
        <div className="conflict__reasoning">
          <strong>Why this controls:</strong> {labelExtractionMethod(obligation.extraction_method)} determined the latest amendment (v{documentMap.get(obligation.document_id)?.version || "?"}) supersedes earlier conflicting terms.
        </div>
      )}
    </section>
  );
}

/* ─── Invoice vs Expected ─────────────────────────────────────────────────── */

function InvoiceComparison({ facts, obligation }) {
  if (!facts || !obligation || !facts.invoices || facts.invoices.length === 0) return null;

  const expectedAmount = facts.contract.base_price * facts.contract.quantity * (1 + obligation.value / 100);
  const effectiveDate = new Date(obligation.effective_date);
  const invoicesAfterEffective = facts.invoices.filter((inv) => new Date(inv.billing_period_start) >= effectiveDate);
  const invoicesToShow = invoicesAfterEffective.length > 0 ? invoicesAfterEffective : facts.invoices.slice(-5);
  const totalGap = invoicesToShow.reduce((sum, inv) => sum + Math.max(expectedAmount - inv.amount_billed, 0), 0);

  return (
    <section className="detail-card detail-card--invoices">
      <div className="detail-card__header">
        <h3>Invoice vs Expected</h3>
        <span className="badge badge--alert">{formatCurrency(totalGap)} total gap</span>
      </div>

      <div className="invoice__summary">
        <div className="invoice__summary-item">
          <span className="invoice__label">Expected (with {obligation.value}% uplift)</span>
          <span className="invoice__value">{formatCurrency(expectedAmount)}/mo</span>
        </div>
        <div className="invoice__summary-item">
          <span className="invoice__label">Actual billed</span>
          <span className="invoice__value">{formatCurrency(invoicesToShow[0]?.amount_billed)}/mo</span>
        </div>
        <div className="invoice__summary-item invoice__summary-item--gap">
          <span className="invoice__label">Gap per month</span>
          <span className="invoice__value invoice__value--alert">
            -{formatCurrency(expectedAmount - (invoicesToShow[0]?.amount_billed || 0))}
          </span>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Period</th><th>Billed</th><th>Expected</th><th>Gap</th></tr>
          </thead>
          <tbody>
            {invoicesToShow.map((invoice) => {
              const gap = expectedAmount - invoice.amount_billed;
              return (
                <tr key={invoice.invoice_id} className={gap > 0 ? "row--alert" : ""}>
                  <td>{formatDate(invoice.billing_period_start)} – {formatDate(invoice.billing_period_end)}</td>
                  <td>{formatCurrency(invoice.amount_billed)}</td>
                  <td>{formatCurrency(expectedAmount)}</td>
                  <td className={gap > 0 ? "cell--alert" : "cell--ok"}>{gap > 0 ? `-${formatCurrency(gap)}` : "✓"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/* ─── Source Documents + Upload ────────────────────────────────────────────── */

function SourceDocuments({ facts, obligation, importing, importMessage, onImport }) {
  const [showUpload, setShowUpload] = useState(false);
  const [documentType, setDocumentType] = useState("amendment");
  const [selectedFile, setSelectedFile] = useState(null);
  const [localError, setLocalError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!selectedFile) { setLocalError("Choose a PDF or DOCX file."); return; }
    try {
      setLocalError("");
      await onImport({ documentType, file: selectedFile });
      setSelectedFile(null);
      setShowUpload(false);
    } catch (err) {
      setLocalError(err.message);
    }
  }

  return (
    <section className="detail-card">
      <div className="detail-card__header">
        <h3>Source Documents</h3>
        <button className="btn btn--sm" type="button" onClick={() => setShowUpload(!showUpload)}>
          {showUpload ? "Cancel" : "+ Upload Document"}
        </button>
      </div>

      {importMessage && (
        <div className="import-banner">
          <p>{importMessage}</p>
        </div>
      )}

      {showUpload && (
        <form className="upload-form" onSubmit={handleSubmit}>
          <label className="upload-form__field">
            <span>Type</span>
            <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
              {DOCUMENT_TYPE_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </label>
          <label className="upload-form__field">
            <span>File</span>
            <input type="file" accept=".pdf,.docx" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
          </label>
          <button className="btn btn--primary" type="submit" disabled={importing}>
            {importing ? "Analyzing…" : "Import & Analyze"}
          </button>
          {localError && <p className="upload-form__error">{localError}</p>}
        </form>
      )}

      <div className="document-list">
        {facts.documents.map((doc) => (
          <div className={`document-row ${obligation?.document_id === doc.document_id ? "document-row--controlling" : ""}`} key={doc.document_id}>
            <span className="document-row__icon">{doc.mime_type === "application/pdf" ? "📄" : "📝"}</span>
            <div className="document-row__info">
              <span className="document-row__name">{doc.file_name}</span>
              <span className="document-row__meta">
                {labelDocumentType(doc.document_type)} · v{doc.version}
                {doc.page_count ? ` · ${doc.page_count}p` : ""}
              </span>
            </div>
            {obligation?.document_id === doc.document_id && <span className="document-row__badge">★ Controls</span>}
            <a className="document-row__link" href={getDocumentContentUrl(doc.document_id)} target="_blank" rel="noreferrer">View</a>
          </div>
        ))}
        {facts.documents.length === 0 && <p className="empty-note">No documents uploaded yet.</p>}
      </div>
    </section>
  );
}

/* ─── AI Brief (Collapsible) ──────────────────────────────────────────────── */

function AIBrief({ brief, loading }) {
  const [expanded, setExpanded] = useState(false);

  if (loading && !brief) return <div className="detail-card"><div className="loading">Generating AI brief…</div></div>;
  if (!brief) return null;

  return (
    <section className="detail-card detail-card--ai">
      <button className="detail-card__header detail-card__header--toggle" type="button" onClick={() => setExpanded(!expanded)}>
        <h3>AI Investigation Brief</h3>
        <span className="toggle-icon">{expanded ? "▾" : "▸"}</span>
      </button>
      {expanded && (
        <div className="ai-brief__content">
          <p className="ai-brief__overview">{brief.overview}</p>
          <div className="ai-brief__grid">
            <div className="ai-brief__block">
              <h4>Root Cause</h4>
              <p>{brief.root_cause}</p>
            </div>
            <div className="ai-brief__block">
              <h4>Recommended Actions</h4>
              <ul>{brief.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}</ul>
            </div>
            <div className="ai-brief__block">
              <h4>Evidence</h4>
              <ul>{brief.evidence_points.map((e, i) => <li key={i}>{e}</li>)}</ul>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

/* ─── Detail Panel ────────────────────────────────────────────────────────── */

function DetailPanel({ selectedType, detail, facts, loading, aiBrief, aiBriefLoading, importing, importMessage, onImport, accountName }) {
  if (loading) return <main className="detail-panel"><div className="loading">Loading…</div></main>;

  // Account selected but no leakage case/prediction yet — show documents + upload
  if (!detail && facts) {
    return (
      <main className="detail-panel">
        <div className="detail-panel__header">
          <div>
            <h2>{accountName || "Account"}</h2>
            <span className="detail-panel__product">{facts.contract.product_name}</span>
          </div>
          <span className="badge badge--lg badge--neutral">No analysis yet</span>
        </div>
        <section className="detail-card">
          <p className="empty-note" style={{padding: "16px", textAlign: "left"}}>
            Upload contract documents to run the leakage analysis. Once the AI processes the documents, this account will appear in the Leakage Cases or At-Risk Predictions queue.
          </p>
        </section>
        <SourceDocuments facts={facts} obligation={null} importing={importing} importMessage={importMessage} onImport={onImport} />
      </main>
    );
  }

  if (!detail || !facts) {
    return (
      <main className="detail-panel">
        <div className="platform-brief">
          <div className="platform-brief__hero">
            <span className="platform-brief__eyebrow">Active agent · Revenue Leakage Investigator</span>
            <h2 className="platform-brief__title">Commercial Execution Intelligence Platform</h2>
            <p className="platform-brief__lead">
              A shared contract evidence layer for post-signature agents. Once a contract is signed, commercial
              intent gets scattered across agreements, amendments, renewal notices, and billing systems — that is
              where revenue starts leaking. This platform reconstructs the controlling commercial term from all
              available documents and turns it into operational action.
            </p>
          </div>

          <div className="platform-brief__cards">
            <div className="platform-brief__card">
              <span className="platform-brief__card-label">Shared platform layer</span>
              <p>Document ingestion, clause extraction, multi-document governing-term resolution, evidence assembly, and AI-generated investigation briefs — shared across every agent on the platform.</p>
            </div>
            <div className="platform-brief__card">
              <span className="platform-brief__card-label">What this agent does</span>
              <p>Detects missed renewal or uplift execution by comparing the controlling contracted rate to what billing operations actually invoiced. Predicts upcoming notice failures before the deadline passes.</p>
            </div>
            <div className="platform-brief__card">
              <span className="platform-brief__card-label">How governing terms are resolved</span>
              <p>The AI reads every document on file — MSA, order forms, amendments, renewal notices — extracts each uplift clause, ranks them by document type and recency, and identifies which one legally controls.</p>
            </div>
            <div className="platform-brief__card">
              <span className="platform-brief__card-label">Next agents on the roadmap</span>
              <p>Quote-to-Contract Drift Detector, Amendment Impact Detector, and Billing vs Contract Mismatch Finder all reuse the same evidence layer without rebuilding ingestion or extraction logic.</p>
            </div>
          </div>

          <div className="platform-brief__select-prompt">
            Select an account from the sidebar to open an investigation →
          </div>
        </div>
      </main>
    );
  }

  const obligation = facts.obligations?.[0];
  const candidateObligations = facts.candidate_obligations || [];

  return (
    <main className="detail-panel">
      <div className="detail-panel__header">
        <div>
          <h2>{detail.account_name}</h2>
          <span className="detail-panel__product">{facts.contract.product_name}</span>
        </div>
        <span className={`badge badge--lg badge--${selectedType === "case" ? "alert" : "warning"}`}>
          {selectedType === "case" ? "Leakage detected" : "At risk"}
        </span>
      </div>

      <FindingSummary selectedType={selectedType} detail={detail} obligation={obligation} />
      <DocumentConflicts obligation={obligation} candidateObligations={candidateObligations} documents={facts.documents} />
      <InvoiceComparison facts={facts} obligation={obligation} />
      <SourceDocuments facts={facts} obligation={obligation} importing={importing} importMessage={importMessage} onImport={onImport} />
      <AIBrief brief={aiBrief} loading={aiBriefLoading} />
    </main>
  );
}

/* ─── App Shell ───────────────────────────────────────────────────────────── */

export default function App() {
  const [aiStatus, setAiStatus] = useState(null);
  const [summary, setSummary] = useState(null);
  const [cases, setCases] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selectedType, setSelectedType] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [facts, setFacts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [aiBrief, setAiBrief] = useState(null);
  const [aiBriefLoading, setAiBriefLoading] = useState(false);
  const [error, setError] = useState("");
  const [documentImporting, setDocumentImporting] = useState(false);
  const [documentImportMessage, setDocumentImportMessage] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadDashboard() {
      try {
        const [aiStatusData, summaryPayload, casePayload, predictionPayload, accountsPayload] = await Promise.all([
          getAIStatus(), getDashboardSummary(), getCases(), getPredictions(), getAccounts(),
        ]);
        if (ignore) return;
        setAiStatus(aiStatusData);
        setSummary(summaryPayload);
        setCases(casePayload);
        setPredictions(predictionPayload);
        setAccounts(accountsPayload);
        // Do not auto-select — show platform brief as landing screen
      } catch (err) {
        if (!ignore) setError(err.message);
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    async function loadDetail(type, id) {
      try {
        setSelectedType(type);
        setSelectedId(id);
        setAiBriefLoading(true);
        const itemDetail = type === "case" ? await getCase(id) : await getPrediction(id);
        const [contractFacts, briefPayload] = await Promise.all([
          getContractFacts(itemDetail.contract_id),
          getContractAIBrief(itemDetail.contract_id, type),
        ]);
        if (!ignore) {
          setDetail(itemDetail);
          setFacts(contractFacts);
          setAiBrief(briefPayload);
        }
      } finally {
        if (!ignore) setAiBriefLoading(false);
      }
    }

    loadDashboard();
    return () => { ignore = true; };
  }, []);

  async function handleSelectCase(item) {
    try {
      setError(""); setDocumentImportMessage(""); setDetailLoading(true); setAiBriefLoading(true);
      setSelectedType("case"); setSelectedId(item.case_id);
      const caseDetail = await getCase(item.case_id);
      const [contractFacts, briefPayload] = await Promise.all([
        getContractFacts(caseDetail.contract_id), getContractAIBrief(caseDetail.contract_id, "case"),
      ]);
      setDetail(caseDetail); setFacts(contractFacts); setAiBrief(briefPayload);
    } catch (err) { setError(err.message); }
    finally { setDetailLoading(false); setAiBriefLoading(false); }
  }

  async function handleSelectPrediction(item) {
    try {
      setError(""); setDocumentImportMessage(""); setDetailLoading(true); setAiBriefLoading(true);
      setSelectedType("prediction"); setSelectedId(item.prediction_id);
      const predDetail = await getPrediction(item.prediction_id);
      const [contractFacts, briefPayload] = await Promise.all([
        getContractFacts(predDetail.contract_id), getContractAIBrief(predDetail.contract_id, "prediction"),
      ]);
      setDetail(predDetail); setFacts(contractFacts); setAiBrief(briefPayload);
    } catch (err) { setError(err.message); }
    finally { setDetailLoading(false); setAiBriefLoading(false); }
  }

  async function handleSelectAccount(item) {
    if (!item.primary_contract_id) return;
    try {
      setError(""); setDocumentImportMessage(""); setDetailLoading(true);
      setSelectedType("account"); setSelectedId(item.account_id);
      setDetail(null); setAiBrief(null);
      const contractFacts = await getContractFacts(item.primary_contract_id);
      setFacts(contractFacts);
    } catch (err) { setError(err.message); }
    finally { setDetailLoading(false); }
  }

  async function handleImportDocument({ documentType, file }) {
    if (!facts) throw new Error("Select a contract first.");
    try {
      setError(""); setDocumentImporting(true); setAiBriefLoading(true);
      const result = await importContractDocument(facts.contract.contract_id, documentType, file);
      const [summaryPayload, casePayload, predictionPayload, accountsPayload, contractFacts, briefPayload] = await Promise.all([
        getDashboardSummary(), getCases(), getPredictions(), getAccounts(),
        getContractFacts(facts.contract.contract_id),
        getContractAIBrief(facts.contract.contract_id, selectedType === "account" ? "contract" : (selectedType || "case")),
      ]);
      setSummary(summaryPayload); setCases(casePayload); setPredictions(predictionPayload); setAccounts(accountsPayload);
      setFacts(contractFacts); setAiBrief(briefPayload);
      setDocumentImportMessage(result.impact?.summary || result.message);
      // If the account now has a case, upgrade the selection
      if (selectedType === "account") {
        const newCase = casePayload.find(c => c.contract_id === facts.contract.contract_id);
        if (newCase) { setSelectedType("case"); setSelectedId(newCase.case_id); setDetail(newCase); }
      }
      if (selectedType === "case") { const r = casePayload.find((i) => i.case_id === selectedId); if (r) setDetail(r); }
      if (selectedType === "prediction") { const r = predictionPayload.find((i) => i.prediction_id === selectedId); if (r) setDetail(r); }
    } catch (err) { setError(err.message); throw err; }
    finally { setDocumentImporting(false); setAiBriefLoading(false); }
  }

  const [view, setView] = useState("investigate");

  if (loading) return <div className="app-shell"><div className="loading-page">Loading…</div></div>;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__left">
          <h1>Commercial Execution Intelligence Platform</h1>
          <span className="topbar__subtitle">{
            view === "drift" ? "Quote-to-Contract Drift Detector" :
            view === "amendments" ? "Amendment Impact Detector" :
            view === "setup" ? "Demo Setup" :
            "Revenue Leakage Investigator"
          }</span>
        </div>
        <nav className="topbar__nav">
          <button
            className={`topbar__nav-btn${view === "investigate" ? " topbar__nav-btn--active" : ""}`}
            onClick={() => setView("investigate")}
          >
            Investigate
          </button>
          <button
            className={`topbar__nav-btn${view === "setup" ? " topbar__nav-btn--active" : ""}`}
            onClick={() => setView("setup")}
          >
            Demo Setup
          </button>
          <button
            className={`topbar__nav-btn${view === "drift" ? " topbar__nav-btn--active" : ""}`}
            onClick={() => setView("drift")}
          >
            Drift Detector
          </button>
          <button
            className={`topbar__nav-btn${view === "amendments" ? " topbar__nav-btn--active" : ""}`}
            onClick={() => setView("amendments")}
          >
            Amendment Impact
          </button>
        </nav>
        <div className="topbar__right">
          <span className={`topbar__ai ${aiStatus?.enabled ? "topbar__ai--on" : ""}`}>
            {aiStatus?.enabled ? `AI: ${aiStatus.model || aiStatus.provider}` : "Rule-based mode"}
          </span>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {view === "setup" ? (
        <SetupPage />
      ) : view === "drift" ? (
        <DriftPage />
      ) : view === "amendments" ? (
        <AmendmentImpactPage />
      ) : (
        <div className="layout">
          <AccountSidebar
            summary={summary}
            cases={cases}
            predictions={predictions}
            accounts={accounts}
            selectedId={selectedId}
            onSelectCase={handleSelectCase}
            onSelectPrediction={handleSelectPrediction}
            onSelectAccount={handleSelectAccount}
          />
          <DetailPanel
            selectedType={selectedType}
            detail={detail}
            facts={facts}
            loading={detailLoading}
            aiBrief={aiBrief}
            aiBriefLoading={aiBriefLoading}
            importing={documentImporting}
            importMessage={documentImportMessage}
            onImport={handleImportDocument}
            accountName={accounts.find(a => a.account_id === selectedId)?.name}
          />
        </div>
      )}
    </div>
  );
}
