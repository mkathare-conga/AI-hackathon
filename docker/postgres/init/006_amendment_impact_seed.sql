-- Seed data for Amendment Impact Detector demo

-- Scenario 1: GlobalTech — amendment increases uplift from 3% to 7% and extends term
INSERT INTO amendment_analyses (analysis_id, contract_id, account_name, amendment_summary, amendment_date, total_changes, high_impact_count, total_annual_revenue_delta, status)
VALUES
    ('amend-analysis-3001', 'amend-ctr-3001', 'GlobalTech Industries', 'Commercial Amendment No. 1 — Revised pricing uplift from 3% to 7% annually, term extended by 12 months, payment terms changed from net 30 to net 45.', '2026-03-15', 4, 2, 86400.00, 'analyzed'),
    ('amend-analysis-3002', 'amend-ctr-3002', 'Cascade Financial Group', 'Amendment No. 2 — Support tier downgraded from premium to standard, seat count reduced from 500 to 400, renewal uplift capped at 2%.', '2026-04-01', 4, 3, -72000.00, 'analyzed'),
    ('amend-analysis-3003', 'amend-ctr-3003', 'Vertex Pharmaceuticals', 'Expansion Amendment — Added Conga Analytics Suite (200 seats), uplift unchanged at 5%, onboarding services included.', '2026-04-20', 3, 1, 180000.00, 'analyzed')
ON CONFLICT (analysis_id) DO NOTHING;

-- GlobalTech impacts
INSERT INTO amendment_impacts (impact_id, analysis_id, contract_id, impact_category, before_value, after_value, severity, annual_revenue_delta, requires_billing_update, requires_workflow_update, explanation, source_clause_text, confidence_score)
VALUES
    ('impact-3001-1', 'amend-analysis-3001', 'amend-ctr-3001', 'renewal_terms_change', '3% annual uplift', '7% annual uplift', 'high', 57600.00, TRUE, TRUE,
     'The annual uplift rate increased from 3% to 7%, adding approximately $57,600 in additional annual revenue at the next renewal. Billing systems must be updated to apply the new rate on the anniversary date.',
     'Section A.1 — The recurring subscription fees shall increase by 7.0% (the "Revised Annual Uplift") on each anniversary of the Effective Date, superseding the prior 3.0% rate.',
     0.97),
    ('impact-3001-2', 'amend-analysis-3001', 'amend-ctr-3001', 'term_extension', 'Ends Dec 31, 2027', 'Ends Dec 31, 2028', 'medium', 28800.00, FALSE, TRUE,
     'The subscription term was extended by 12 months, locking in the customer for an additional year. This guarantees $28,800 in additional committed revenue but delays renewal negotiation.',
     'Section A.3 — The Subscription Term is hereby extended through December 31, 2028.',
     0.95),
    ('impact-3001-3', 'amend-analysis-3001', 'amend-ctr-3001', 'payment_terms_change', 'Net 30 days', 'Net 45 days', 'low', 0.00, TRUE, FALSE,
     'Payment terms extended from net 30 to net 45 days. No direct revenue impact, but increases days sales outstanding (DSO) and working capital requirements.',
     'Section A.4 — Payment is due net forty-five (45) days from invoice date.',
     0.98),
    ('impact-3001-4', 'amend-analysis-3001', 'amend-ctr-3001', 'scope_addition', 'No API access', 'API access included', 'medium', 0.00, FALSE, TRUE,
     'API access added to the subscription at no additional charge. While no direct revenue impact, this expands the service commitment and may require provisioning changes.',
     'Section A.5 — Customer is granted access to the standard API tier at no additional fee.',
     0.92)
ON CONFLICT (impact_id) DO NOTHING;

-- Cascade Financial impacts
INSERT INTO amendment_impacts (impact_id, analysis_id, contract_id, impact_category, before_value, after_value, severity, annual_revenue_delta, requires_billing_update, requires_workflow_update, explanation, source_clause_text, confidence_score)
VALUES
    ('impact-3002-1', 'amend-analysis-3002', 'amend-ctr-3002', 'support_change', 'Premium (24/7)', 'Standard (business hours)', 'high', -24000.00, TRUE, TRUE,
     'Support tier downgraded from premium (24/7 with dedicated CSM) to standard business-hours support. This reduces the monthly support charge by $2,000 and removes the dedicated customer success resource.',
     'Section 3.1 — Support services are revised to Standard Tier (business hours, Monday through Friday).',
     0.96),
    ('impact-3002-2', 'amend-analysis-3002', 'amend-ctr-3002', 'quantity_change', '500 seats', '400 seats', 'high', -36000.00, TRUE, FALSE,
     'Licensed seat count reduced from 500 to 400. This directly removes $36,000 in annual recurring revenue and may indicate customer contraction.',
     'Section 1.1 — Licensed seats: 400 named-user subscriptions (reduced from 500).',
     0.98),
    ('impact-3002-3', 'amend-analysis-3002', 'amend-ctr-3002', 'renewal_terms_change', '5% annual uplift', '2% annual uplift (capped)', 'high', -12000.00, TRUE, TRUE,
     'The annual renewal uplift was reduced from 5% to a 2% cap. This limits future pricing power and reduces projected year-over-year revenue growth by approximately $12,000.',
     'Section 2.3 — Annual price adjustment shall not exceed 2% per annum, notwithstanding any prior language.',
     0.97),
    ('impact-3002-4', 'amend-analysis-3002', 'amend-ctr-3002', 'liability_change', 'Standard liability cap (12 months fees)', 'Enhanced liability cap (24 months fees)', 'medium', 0.00, FALSE, FALSE,
     'Liability cap increased from 12 months to 24 months of fees paid. No direct revenue impact but increases commercial risk exposure.',
     'Section 7.1 — Aggregate liability shall not exceed fees paid during the twenty-four (24) month period preceding the claim.',
     0.93)
ON CONFLICT (impact_id) DO NOTHING;

-- Vertex Pharmaceuticals impacts
INSERT INTO amendment_impacts (impact_id, analysis_id, contract_id, impact_category, before_value, after_value, severity, annual_revenue_delta, requires_billing_update, requires_workflow_update, explanation, source_clause_text, confidence_score)
VALUES
    ('impact-3003-1', 'amend-analysis-3003', 'amend-ctr-3003', 'scope_addition', 'Conga CLM only', 'Conga CLM + Analytics Suite (200 seats)', 'high', 180000.00, TRUE, TRUE,
     'Conga Analytics Suite added with 200 seats at $75/seat/month. This expansion adds $180,000 in new annual recurring revenue and requires provisioning of the analytics module.',
     'Section 1.2 — Customer subscribes to Conga Analytics Suite for 200 seats at $75.00 per seat per month.',
     0.98),
    ('impact-3003-2', 'amend-analysis-3003', 'amend-ctr-3003', 'scope_addition', 'No onboarding', 'Onboarding included (40 hours)', 'low', 0.00, FALSE, TRUE,
     'Implementation/onboarding services (40 hours) included at no additional charge as part of the expansion deal. Professional services team needs to be scheduled.',
     'Section 4.1 — Supplier will provide up to forty (40) hours of onboarding and configuration assistance at no additional charge.',
     0.95),
    ('impact-3003-3', 'amend-analysis-3003', 'amend-ctr-3003', 'term_extension', 'Ends Dec 31, 2027', 'Ends Dec 31, 2028', 'medium', 0.00, FALSE, TRUE,
     'Subscription term co-terminated with the expansion, extending through December 31, 2028. Both products now renew together, simplifying administration.',
     'Section 2.1 — The Subscription Term for all products is co-terminated through December 31, 2028.',
     0.94)
ON CONFLICT (impact_id) DO NOTHING;

-- Action items for GlobalTech
INSERT INTO amendment_action_items (action_id, analysis_id, impact_id, action_type, description, priority, status, assigned_team)
VALUES
    ('action-3001-1', 'amend-analysis-3001', 'impact-3001-1', 'update_billing', 'Update billing system to apply 7% uplift rate on next anniversary (was 3%).', 'urgent', 'open', 'Revenue Operations'),
    ('action-3001-2', 'amend-analysis-3001', 'impact-3001-1', 'update_renewal_workflow', 'Update renewal workflow to use new 7% uplift and confirm notice was sent.', 'high', 'open', 'Revenue Operations'),
    ('action-3001-3', 'amend-analysis-3001', 'impact-3001-2', 'update_renewal_workflow', 'Adjust contract end date in CRM to Dec 31, 2028. Renewal reminders will shift.', 'medium', 'open', 'Sales Operations'),
    ('action-3001-4', 'amend-analysis-3001', 'impact-3001-3', 'update_billing', 'Change payment terms in invoicing system from net 30 to net 45.', 'medium', 'open', 'Finance'),
    ('action-3001-5', 'amend-analysis-3001', 'impact-3001-4', 'update_provisioning', 'Enable API access tier for GlobalTech in the provisioning system.', 'medium', 'open', 'Engineering')
ON CONFLICT (action_id) DO NOTHING;

-- Action items for Cascade
INSERT INTO amendment_action_items (action_id, analysis_id, impact_id, action_type, description, priority, status, assigned_team)
VALUES
    ('action-3002-1', 'amend-analysis-3002', 'impact-3002-1', 'update_support_tier', 'Downgrade Cascade from premium to standard support in the ticketing system. Remove dedicated CSM assignment.', 'urgent', 'open', 'Customer Success'),
    ('action-3002-2', 'amend-analysis-3002', 'impact-3002-2', 'update_billing', 'Reduce licensed seat count from 500 to 400 in billing system. Issue credit for overpayment if applicable.', 'urgent', 'open', 'Revenue Operations'),
    ('action-3002-3', 'amend-analysis-3002', 'impact-3002-2', 'update_provisioning', 'Deprovision 100 seats. Notify affected users before deactivation.', 'high', 'open', 'Engineering'),
    ('action-3002-4', 'amend-analysis-3002', 'impact-3002-3', 'update_billing', 'Update renewal uplift rate from 5% to 2% cap in billing configuration.', 'high', 'open', 'Revenue Operations'),
    ('action-3002-5', 'amend-analysis-3002', 'impact-3002-4', 'legal_review', 'Review increased liability exposure (24 months vs 12 months) with legal team.', 'medium', 'open', 'Legal')
ON CONFLICT (action_id) DO NOTHING;

-- Action items for Vertex
INSERT INTO amendment_action_items (action_id, analysis_id, impact_id, action_type, description, priority, status, assigned_team)
VALUES
    ('action-3003-1', 'amend-analysis-3003', 'impact-3003-1', 'update_billing', 'Add Conga Analytics Suite (200 seats × $75/seat/mo) to Vertex billing record.', 'urgent', 'open', 'Revenue Operations'),
    ('action-3003-2', 'amend-analysis-3003', 'impact-3003-1', 'update_provisioning', 'Provision Conga Analytics Suite for 200 users. Coordinate with Vertex IT team for SSO setup.', 'high', 'open', 'Engineering'),
    ('action-3003-3', 'amend-analysis-3003', 'impact-3003-2', 'update_provisioning', 'Schedule 40 hours of onboarding with professional services team. Contact customer to set dates.', 'high', 'open', 'Professional Services'),
    ('action-3003-4', 'amend-analysis-3003', 'impact-3003-3', 'update_renewal_workflow', 'Update contract end date to Dec 31, 2028 for co-termination across all products.', 'medium', 'open', 'Sales Operations')
ON CONFLICT (action_id) DO NOTHING;
