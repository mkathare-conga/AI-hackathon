-- Quote-to-Contract Drift Detector schema

CREATE TABLE IF NOT EXISTS quotes (
    quote_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    opportunity_name TEXT NOT NULL,
    created_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'approved'
);

CREATE TABLE IF NOT EXISTS quote_lines (
    line_id TEXT PRIMARY KEY,
    quote_id TEXT NOT NULL REFERENCES quotes(quote_id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    discount_percent NUMERIC(5, 2) NOT NULL DEFAULT 0,
    support_tier TEXT NOT NULL DEFAULT 'standard',
    renewal_uplift_percent NUMERIC(5, 2),
    payment_terms_days INTEGER NOT NULL DEFAULT 30,
    currency TEXT NOT NULL DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS drift_contracts (
    contract_id TEXT PRIMARY KEY,
    quote_id TEXT NOT NULL REFERENCES quotes(quote_id) ON DELETE CASCADE,
    contract_text TEXT NOT NULL,
    signed_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS drift_findings (
    finding_id TEXT PRIMARY KEY,
    quote_id TEXT NOT NULL REFERENCES quotes(quote_id) ON DELETE CASCADE,
    contract_id TEXT NOT NULL REFERENCES drift_contracts(contract_id) ON DELETE CASCADE,
    drift_type TEXT NOT NULL,
    attribute_name TEXT NOT NULL,
    quote_value TEXT NOT NULL,
    contract_value TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    estimated_annual_impact NUMERIC(12, 2),
    explanation TEXT NOT NULL,
    source_clause_text TEXT,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.9,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quote_lines_quote_id ON quote_lines(quote_id);
CREATE INDEX IF NOT EXISTS idx_drift_contracts_quote_id ON drift_contracts(quote_id);
CREATE INDEX IF NOT EXISTS idx_drift_findings_quote_id ON drift_findings(quote_id);
CREATE INDEX IF NOT EXISTS idx_drift_findings_contract_id ON drift_findings(contract_id);
