-- Amendment Impact Detector schema

CREATE TABLE IF NOT EXISTS amendment_analyses (
    analysis_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL,
    account_name TEXT NOT NULL,
    amendment_summary TEXT NOT NULL,
    amendment_date DATE NOT NULL,
    total_changes INT NOT NULL DEFAULT 0,
    high_impact_count INT NOT NULL DEFAULT 0,
    total_annual_revenue_delta NUMERIC(12, 2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'analyzed' CHECK (status IN ('pending', 'analyzed', 'acknowledged')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS amendment_impacts (
    impact_id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL REFERENCES amendment_analyses(analysis_id) ON DELETE CASCADE,
    contract_id TEXT NOT NULL,
    impact_category TEXT NOT NULL CHECK (impact_category IN (
        'pricing_change', 'quantity_change', 'term_extension', 'term_reduction',
        'support_change', 'scope_addition', 'scope_removal', 'renewal_terms_change',
        'payment_terms_change', 'liability_change', 'sla_change'
    )),
    before_value TEXT NOT NULL,
    after_value TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    annual_revenue_delta NUMERIC(12, 2),
    requires_billing_update BOOLEAN NOT NULL DEFAULT FALSE,
    requires_workflow_update BOOLEAN NOT NULL DEFAULT FALSE,
    explanation TEXT NOT NULL,
    source_clause_text TEXT,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.9,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS amendment_action_items (
    action_id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL REFERENCES amendment_analyses(analysis_id) ON DELETE CASCADE,
    impact_id TEXT REFERENCES amendment_impacts(impact_id) ON DELETE SET NULL,
    action_type TEXT NOT NULL CHECK (action_type IN (
        'update_billing', 'update_renewal_workflow', 'notify_customer',
        'update_support_tier', 'review_sla', 'update_provisioning', 'legal_review'
    )),
    description TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('urgent', 'high', 'medium', 'low')),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'completed', 'dismissed')),
    assigned_team TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_amendment_analyses_contract_id ON amendment_analyses(contract_id);
CREATE INDEX IF NOT EXISTS idx_amendment_impacts_analysis_id ON amendment_impacts(analysis_id);
CREATE INDEX IF NOT EXISTS idx_amendment_action_items_analysis_id ON amendment_action_items(analysis_id);
