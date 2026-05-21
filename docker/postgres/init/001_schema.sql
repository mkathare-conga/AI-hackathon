CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contracts (
    contract_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    product_name TEXT NOT NULL,
    term_start DATE NOT NULL,
    term_end DATE NOT NULL,
    base_price NUMERIC(12, 2) NOT NULL,
    currency TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    raw_contract_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contract_documents (
    document_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL REFERENCES contracts(contract_id) ON DELETE CASCADE,
    document_type TEXT NOT NULL CHECK (document_type IN ('msa', 'nda', 'order_form', 'amendment', 'renewal_notice')),
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    storage_key TEXT NOT NULL UNIQUE,
    version INTEGER NOT NULL DEFAULT 1,
    page_count INTEGER,
    extracted_text TEXT,
    commercial_excerpt TEXT,
    ingestion_status TEXT NOT NULL CHECK (ingestion_status IN ('pending_upload', 'registered', 'uploaded', 'parsed', 'failed')),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoice_lines (
    invoice_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    contract_id TEXT NOT NULL REFERENCES contracts(contract_id),
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    amount_billed NUMERIC(12, 2) NOT NULL,
    quantity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS renewal_events (
    contract_id TEXT NOT NULL REFERENCES contracts(contract_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('notice_sent', 'renewal_started', 'renewal_closed')),
    event_date DATE NOT NULL,
    PRIMARY KEY (contract_id, event_type, event_date)
);

CREATE TABLE IF NOT EXISTS obligation_extractions (
    extraction_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL REFERENCES contracts(contract_id) ON DELETE CASCADE,
    document_id TEXT REFERENCES contract_documents(document_id) ON DELETE SET NULL,
    obligation_type TEXT NOT NULL,
    value NUMERIC(12, 2) NOT NULL,
    effective_date DATE,
    notice_window_days INTEGER,
    source_clause_text TEXT NOT NULL,
    page_number INTEGER,
    confidence_score DOUBLE PRECISION NOT NULL,
    extraction_method TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contracts_account_id ON contracts(account_id);
CREATE INDEX IF NOT EXISTS idx_contract_documents_contract_id ON contract_documents(contract_id);
CREATE INDEX IF NOT EXISTS idx_invoice_lines_contract_id ON invoice_lines(contract_id);
CREATE INDEX IF NOT EXISTS idx_renewal_events_contract_id ON renewal_events(contract_id);
CREATE INDEX IF NOT EXISTS idx_obligation_extractions_contract_id ON obligation_extractions(contract_id);
CREATE INDEX IF NOT EXISTS idx_obligation_extractions_document_id ON obligation_extractions(document_id);