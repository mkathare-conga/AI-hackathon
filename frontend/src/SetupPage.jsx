import React, { useState, useEffect, useCallback } from "react";
import {
  setupListAccounts, setupCreateAccount, setupDeleteAccount,
  setupListContracts, setupCreateContract, setupDeleteContract,
  setupListInvoices, setupCreateInvoice, setupDeleteInvoice,
  setupReset, setupShiftRenewal,
} from "./api.js";

/* ─── Helpers ─────────────────────────────────────────────────────────────── */
function fmt(n) {
  return Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function firstOfMonth(monthsAgo = 0) {
  const d = new Date();
  d.setDate(1);
  d.setMonth(d.getMonth() - monthsAgo);
  return d.toISOString().slice(0, 10);
}

function lastOfMonth(monthsAgo = 0) {
  const d = new Date();
  d.setDate(1);
  d.setMonth(d.getMonth() - monthsAgo + 1);
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

/* ─── Panel wrapper ───────────────────────────────────────────────────────── */
function Panel({ title, subtitle, children }) {
  return (
    <div className="setup-panel">
      <div className="setup-panel__head">
        <span className="setup-panel__title">{title}</span>
        {subtitle && <span className="setup-panel__subtitle">{subtitle}</span>}
      </div>
      {children}
    </div>
  );
}

/* ─── Inline error / status ───────────────────────────────────────────────── */
function Msg({ msg, isError }) {
  if (!msg) return null;
  return <div className={isError ? "setup-msg setup-msg--error" : "setup-msg setup-msg--ok"}>{msg}</div>;
}

/* ─── Delete button ───────────────────────────────────────────────────────── */
function DelBtn({ onClick, label = "Delete" }) {
  return (
    <button className="setup-del-btn" onClick={onClick} title={label}>✕</button>
  );
}

/* ─── Accounts Panel ──────────────────────────────────────────────────────── */
function AccountsPanel({ selectedId, onSelect }) {
  const [accounts, setAccounts] = useState([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [isErr, setIsErr] = useState(false);

  const load = useCallback(async () => {
    const data = await setupListAccounts();
    setAccounts(data);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true); setMsg(""); setIsErr(false);
    try {
      await setupCreateAccount(name.trim());
      setName("");
      setMsg("Account created.");
      await load();
    } catch (err) {
      setMsg(err.message); setIsErr(true);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(accountId, e) {
    e.stopPropagation();
    if (!confirm("Delete this account and all its contracts, invoices, and documents?")) return;
    try {
      await setupDeleteAccount(accountId);
      if (selectedId === accountId) onSelect(null);
      await load();
    } catch (err) {
      setMsg(err.message); setIsErr(true);
    }
  }

  return (
    <Panel title="Accounts" subtitle={`${accounts.length} total`}>
      <div className="setup-list">
        {accounts.length === 0 && <div className="setup-empty">No accounts yet.</div>}
        {accounts.map(a => (
          <div
            key={a.account_id}
            className={`setup-row${selectedId === a.account_id ? " setup-row--selected" : ""}`}
            onClick={() => onSelect(a.account_id)}
          >
            <div className="setup-row__main">
              <span className="setup-row__name">{a.name}</span>
              <span className="setup-row__meta">{a.account_id}</span>
            </div>
            <div className="setup-row__badges">
              <span className="setup-badge">{a.contract_count} contracts</span>
              <span className="setup-badge">{a.invoice_count} invoices</span>
            </div>
            <DelBtn onClick={(e) => handleDelete(a.account_id, e)} label="Delete account" />
          </div>
        ))}
      </div>

      <form className="setup-form" onSubmit={handleCreate}>
        <div className="setup-form__row">
          <input
            className="setup-input"
            placeholder="Account name"
            value={name}
            onChange={e => setName(e.target.value)}
            required
          />
          <button className="setup-btn" disabled={busy}>
            {busy ? "Creating…" : "+ Add Account"}
          </button>
        </div>
        <Msg msg={msg} isError={isErr} />
      </form>
    </Panel>
  );
}

/* ─── Contracts Panel ─────────────────────────────────────────────────────── */
function ContractsPanel({ accountId, selectedId, onSelect }) {
  const [contracts, setContracts] = useState([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [isErr, setIsErr] = useState(false);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    product_name: "",
    term_start: firstOfMonth(12),
    term_end: firstOfMonth(-12),
    base_price: "",
    currency: "USD",
    quantity: "1",
    uplift_pct: "5",
  });

  // renewal editor state
  const [editingRenewal, setEditingRenewal] = useState(null);  // contract_id being edited
  const [renewalDays, setRenewalDays] = useState("");
  const [renewalBusy, setRenewalBusy] = useState(false);

  const load = useCallback(async () => {
    if (!accountId) { setContracts([]); return; }
    const data = await setupListContracts(accountId);
    setContracts(data);
  }, [accountId]);

  useEffect(() => { load(); setOpen(false); setMsg(""); }, [load]);

  function setField(k, v) { setForm(f => ({ ...f, [k]: v })); }

  async function handleCreate(e) {
    e.preventDefault();
    setBusy(true); setMsg(""); setIsErr(false);
    try {
      await setupCreateContract(accountId, form);
      setOpen(false);
      setMsg("Contract created.");
      await load();
    } catch (err) {
      setMsg(err.message); setIsErr(true);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(contractId, e) {
    e.stopPropagation();
    if (!confirm("Delete this contract and all its invoice lines and documents?")) return;
    try {
      await setupDeleteContract(contractId);
      if (selectedId === contractId) onSelect(null);
      await load();
    } catch (err) {
      setMsg(err.message); setIsErr(true);
    }
  }

  function openRenewalEditor(contractId, currentDays, e) {
    e.stopPropagation();
    setEditingRenewal(contractId);
    setRenewalDays(currentDays !== null && currentDays !== undefined ? String(Math.max(currentDays, 0)) : "30");
  }

  async function handleShiftRenewal(contractId, e) {
    e.preventDefault();
    const days = parseInt(renewalDays, 10);
    if (isNaN(days) || days < 0) return;
    setRenewalBusy(true);
    try {
      await setupShiftRenewal(contractId, days);
      setEditingRenewal(null);
      await load();
    } catch (err) {
      setMsg(err.message); setIsErr(true);
    } finally {
      setRenewalBusy(false);
    }
  }

  function daysColor(days) {
    if (days === null || days === undefined) return "neutral";
    if (days <= 0) return "red";
    if (days <= 7) return "orange";
    if (days <= 30) return "yellow";
    return "green";
  }

  if (!accountId) {
    return (
      <Panel title="Contracts">
        <div className="setup-empty setup-empty--locked">← Select an account first</div>
      </Panel>
    );
  }

  return (
    <Panel title="Contracts" subtitle={`${contracts.length} for selected account`}>
      <div className="setup-list">
        {contracts.length === 0 && <div className="setup-empty">No contracts yet.</div>}
        {contracts.map(c => (
          <div
            key={c.contract_id}
            className={`setup-row${selectedId === c.contract_id ? " setup-row--selected" : ""}`}
            onClick={() => onSelect(c.contract_id, c.account_id)}
          >
            <div className="setup-row__main">
              <span className="setup-row__name">{c.product_name}</span>
              <span className="setup-row__meta">{c.contract_id}</span>
            </div>
            <div className="setup-row__badges">
              <span className="setup-badge">{c.currency} {fmt(c.base_price)} × {c.quantity}</span>
              <span className="setup-badge">{c.term_start} → {c.term_end}</span>
              <span className="setup-badge">{c.invoice_count} invoices</span>
              {c.days_until_deadline !== null && c.days_until_deadline !== undefined && (
                editingRenewal === c.contract_id ? (
                  <form
                    className="renewal-editor"
                    onSubmit={(e) => handleShiftRenewal(c.contract_id, e)}
                    onClick={e => e.stopPropagation()}
                  >
                    <input
                      className="renewal-editor__input"
                      type="number"
                      min="0"
                      value={renewalDays}
                      onChange={e => setRenewalDays(e.target.value)}
                      autoFocus
                      placeholder="days"
                    />
                    <span className="renewal-editor__label">days left</span>
                    <button className="renewal-editor__save" type="submit" disabled={renewalBusy}>
                      {renewalBusy ? "…" : "Set"}
                    </button>
                    <button
                      className="renewal-editor__cancel"
                      type="button"
                      onClick={e => { e.stopPropagation(); setEditingRenewal(null); }}
                    >✕</button>
                  </form>
                ) : (
                  <button
                    className={`renewal-badge renewal-badge--${daysColor(c.days_until_deadline)}`}
                    onClick={(e) => openRenewalEditor(c.contract_id, c.days_until_deadline, e)}
                    title="Click to adjust days until notice deadline"
                  >
                    ⏰ {c.days_until_deadline <= 0 ? "Overdue" : `${c.days_until_deadline}d left`}
                  </button>
                )
              )}
            </div>
            <DelBtn onClick={(e) => handleDelete(c.contract_id, e)} label="Delete contract" />
          </div>
        ))}
      </div>

      <Msg msg={msg} isError={isErr} />

      {!open ? (
        <button className="setup-btn setup-btn--ghost" onClick={() => setOpen(true)}>+ Add Contract</button>
      ) : (
        <form className="setup-form setup-form--stack" onSubmit={handleCreate}>
          <div className="setup-form__row">
            <input className="setup-input setup-input--wide" placeholder="Product / subscription name" value={form.product_name}
              onChange={e => setField("product_name", e.target.value)} required />
          </div>
          <div className="setup-form__row">
            <label className="setup-label">Term start</label>
            <input type="date" className="setup-input" value={form.term_start}
              onChange={e => setField("term_start", e.target.value)} required />
            <label className="setup-label">Term end</label>
            <input type="date" className="setup-input" value={form.term_end}
              onChange={e => setField("term_end", e.target.value)} required />
          </div>
          <div className="setup-form__row">
            <label className="setup-label">Base price</label>
            <input type="number" className="setup-input" placeholder="10000" value={form.base_price}
              onChange={e => setField("base_price", e.target.value)} required min="0" step="0.01" />
            <select className="setup-select" value={form.currency} onChange={e => setField("currency", e.target.value)}>
              <option>USD</option><option>EUR</option><option>GBP</option>
            </select>
            <label className="setup-label">Qty</label>
            <input type="number" className="setup-input setup-input--sm" placeholder="1" value={form.quantity}
              onChange={e => setField("quantity", e.target.value)} required min="1" />
          </div>
          <div className="setup-form__row">
            <label className="setup-label">Uplift %</label>
            <input type="number" className="setup-input setup-input--sm" placeholder="5" value={form.uplift_pct}
              onChange={e => setField("uplift_pct", e.target.value)} min="0" max="100" step="0.1" />
            <span className="setup-hint">Written into the contract's clause text</span>
          </div>
          <div className="setup-form__row">
            <button className="setup-btn" disabled={busy}>{busy ? "Creating…" : "Create Contract"}</button>
            <button type="button" className="setup-btn setup-btn--ghost" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </form>
      )}
    </Panel>
  );
}

/* ─── Invoice Lines Panel ─────────────────────────────────────────────────── */
function InvoicesPanel({ contractId, accountId }) {
  const [invoices, setInvoices] = useState([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [isErr, setIsErr] = useState(false);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    billing_period_start: firstOfMonth(1),
    billing_period_end: lastOfMonth(1),
    amount_billed: "",
    quantity: "1",
  });

  const load = useCallback(async () => {
    if (!contractId) { setInvoices([]); return; }
    const data = await setupListInvoices(contractId);
    setInvoices(data);
  }, [contractId]);

  useEffect(() => { load(); setOpen(false); setMsg(""); }, [load]);

  function setField(k, v) { setForm(f => ({ ...f, [k]: v })); }

  async function handleCreate(e) {
    e.preventDefault();
    setBusy(true); setMsg(""); setIsErr(false);
    try {
      await setupCreateInvoice(contractId, { ...form, account_id: accountId });
      setOpen(false);
      setMsg("Invoice line added.");
      await load();
    } catch (err) {
      setMsg(err.message); setIsErr(true);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(invoiceId) {
    try {
      await setupDeleteInvoice(invoiceId);
      await load();
    } catch (err) {
      setMsg(err.message); setIsErr(true);
    }
  }

  const total = invoices.reduce((s, i) => s + Number(i.amount_billed), 0);

  if (!contractId) {
    return (
      <Panel title="Invoice Lines">
        <div className="setup-empty setup-empty--locked">← Select a contract first</div>
      </Panel>
    );
  }

  return (
    <Panel title="Invoice Lines" subtitle={invoices.length > 0 ? `${invoices.length} lines · $${fmt(total)} total billed` : undefined}>
      <div className="setup-list">
        {invoices.length === 0 && <div className="setup-empty">No invoice lines yet.</div>}
        {invoices.map(inv => (
          <div key={inv.invoice_id} className="setup-row">
            <div className="setup-row__main">
              <span className="setup-row__name">{inv.billing_period_start} → {inv.billing_period_end}</span>
              <span className="setup-row__meta">{inv.invoice_id}</span>
            </div>
            <div className="setup-row__badges">
              <span className="setup-badge setup-badge--amount">${fmt(inv.amount_billed)}</span>
              <span className="setup-badge">qty {inv.quantity}</span>
            </div>
            <DelBtn onClick={() => handleDelete(inv.invoice_id)} label="Delete invoice line" />
          </div>
        ))}
      </div>

      <Msg msg={msg} isError={isErr} />

      {!open ? (
        <button className="setup-btn setup-btn--ghost" onClick={() => setOpen(true)}>+ Add Invoice Line</button>
      ) : (
        <form className="setup-form setup-form--stack" onSubmit={handleCreate}>
          <div className="setup-form__row">
            <label className="setup-label">Period start</label>
            <input type="date" className="setup-input" value={form.billing_period_start}
              onChange={e => setField("billing_period_start", e.target.value)} required />
            <label className="setup-label">Period end</label>
            <input type="date" className="setup-input" value={form.billing_period_end}
              onChange={e => setField("billing_period_end", e.target.value)} required />
          </div>
          <div className="setup-form__row">
            <label className="setup-label">Amount billed</label>
            <input type="number" className="setup-input" placeholder="10000.00" value={form.amount_billed}
              onChange={e => setField("amount_billed", e.target.value)} required min="0" step="0.01" />
            <label className="setup-label">Qty</label>
            <input type="number" className="setup-input setup-input--sm" value={form.quantity}
              onChange={e => setField("quantity", e.target.value)} required min="1" />
          </div>
          <div className="setup-form__row">
            <button className="setup-btn" disabled={busy}>{busy ? "Saving…" : "Add Invoice Line"}</button>
            <button type="button" className="setup-btn setup-btn--ghost" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </form>
      )}
    </Panel>
  );
}

/* ─── SetupPage ───────────────────────────────────────────────────────────── */
export default function SetupPage() {
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [selectedContract, setSelectedContract] = useState(null);
  const [selectedContractAccountId, setSelectedContractAccountId] = useState(null);

  function handleSelectAccount(id) {
    setSelectedAccount(id);
    setSelectedContract(null);
    setSelectedContractAccountId(null);
  }

  function handleSelectContract(contractId, accountId) {
    setSelectedContract(contractId);
    setSelectedContractAccountId(accountId || selectedAccount);
  }

  const [resetting, setResetting] = useState(false);
  const [resetMsg, setResetMsg] = useState("");

  async function handleReset() {
    if (!window.confirm(
      "Reset all demo data to the default seed?\n\nThis will delete any accounts, contracts, invoices, and uploaded documents you have added, and restore the original 6 accounts."
    )) return;
    setResetting(true);
    setResetMsg("");
    try {
      await setupReset();
      setSelectedAccount(null);
      setSelectedContract(null);
      setSelectedContractAccountId(null);
      setResetMsg("Reset complete — data restored to defaults.");
      setTimeout(() => setResetMsg(""), 4000);
    } catch (err) {
      setResetMsg("Reset failed: " + err.message);
    } finally {
      setResetting(false);
    }
  }

  return (
    <div className="setup-page">
      <div className="setup-header">
        <div className="setup-header__row">
          <h2 className="setup-header__title">Demo Setup</h2>
          <button
            className={`setup-reset-btn${resetting ? " setup-reset-btn--busy" : ""}`}
            onClick={handleReset}
            disabled={resetting}
          >
            {resetting ? "Resetting…" : "↺ Reset to Default"}
          </button>
        </div>
        <p className="setup-header__desc">
          Create accounts, contracts, and invoice lines for the demo. Uploaded documents are managed from the Investigator view.
        </p>
        {resetMsg && <p className="setup-reset-msg">{resetMsg}</p>}
      </div>
      <div className="setup-columns">
        <AccountsPanel selectedId={selectedAccount} onSelect={handleSelectAccount} />
        <ContractsPanel accountId={selectedAccount} selectedId={selectedContract} onSelect={handleSelectContract} />
        <InvoicesPanel contractId={selectedContract} accountId={selectedContractAccountId} />
      </div>
    </div>
  );
}
