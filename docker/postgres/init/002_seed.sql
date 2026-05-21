INSERT INTO accounts (account_id, name)
VALUES
    ('acc-1001', 'Northwind Manufacturing'),
    ('acc-1002', 'Apex Health Systems'),
    ('acc-1003', 'BluePeak Retail'),
    ('acc-1004', 'Summit Distribution Group'),
    ('acc-1005', 'Redwood BioLabs'),
    ('acc-2001', 'Pinnacle Logistics')
ON CONFLICT (account_id) DO UPDATE SET
    name = EXCLUDED.name;

INSERT INTO contracts (
    contract_id,
    account_id,
    product_name,
    term_start,
    term_end,
    base_price,
    currency,
    quantity,
    raw_contract_text
)
VALUES
    (
        'ctr-1001',
        'acc-1001',
        'Conga CLM Enterprise',
        DATE '2025-01-01',
        DATE '2027-12-31',
        100.00,
        'USD',
        1000,
        $ctr1001$MASTER SUBSCRIPTION AGREEMENT

This Master Subscription Agreement ("Agreement") is entered into as of January 1, 2025, by and between Conga Software, Inc. ("Supplier") and Northwind Manufacturing, Inc. ("Customer"). This Agreement governs Customer's access to and use of Conga CLM Enterprise, related support services, and any order forms executed by the parties.

1. Subscription Term and Renewal. The initial subscription term begins on January 1, 2025 and continues through December 31, 2025. Thereafter, the subscription will automatically renew for successive twelve-month renewal terms unless either party provides written notice of non-renewal in accordance with this Agreement.

2. Fees and Invoicing. Customer will be invoiced monthly for 1,000 subscribed units at the pricing set forth in the applicable order form. Undisputed invoices are due net thirty (30) days from receipt.

3. Renewal Pricing Adjustment. Beginning with the first renewal term and on each subsequent renewal anniversary, the subscription fees are subject to a 5% annual price increase. Supplier may implement the 5% annual price increase by providing Customer at least 30 days notice prior to the applicable renewal anniversary.

4. Support and Service Levels. Supplier will provide standard support during normal business hours and will use commercially reasonable efforts to maintain service availability in accordance with the support policy incorporated by reference.

5. General Terms. This Agreement, together with each order form, constitutes the entire agreement between the parties with respect to the subject matter hereof and supersedes all prior or contemporaneous agreements, proposals, and communications, whether written or oral.$ctr1001$
    ),
    (
        'ctr-1002',
        'acc-1002',
        'Conga Composer Premium',
        DATE '2025-06-01',
        DATE '2027-05-31',
        250.00,
        'USD',
        150,
        $ctr1002$SOFTWARE SUBSCRIPTION AND SERVICES AGREEMENT

This Software Subscription and Services Agreement is effective June 1, 2025, between Conga Software, Inc. and Apex Health Systems LLC. The parties agree that Supplier will provide access to Conga Composer Premium for internal business use subject to the terms and conditions below.

1. Scope of Subscription. Customer is purchasing 150 named-user subscriptions together with standard implementation assistance and access to generally available product updates during the subscription term.

2. Term. The initial term commences on June 1, 2025 and ends on May 31, 2026. The Agreement will renew automatically for additional one-year periods unless either party delivers notice of non-renewal before the renewal date.

3. Charges and Payment. Subscription charges will be billed monthly in arrears. Customer shall pay all undisputed amounts within thirty (30) days after the invoice date.

4. Annual Uplift. Commencing on the first renewal date and each renewal term thereafter, the recurring subscription charges will include a 5% annual uplift. Supplier may apply the 5% annual uplift provided Supplier gives Customer no less than 30 days notice before the renewal date.

5. Compliance and Security. Customer remains responsible for its users and for compliance with applicable healthcare and privacy obligations related to Customer data processed within the service.$ctr1002$
    ),
    (
        'ctr-1003',
        'acc-1003',
        'Conga Orchestrate Standard',
        DATE '2025-03-15',
        DATE '2027-03-14',
        180.00,
        'USD',
        80,
        $ctr1003$ORDER FORM TERMS AND CONDITIONS

This Order Form and the Master Subscription Agreement between Conga Software, Inc. and BluePeak Retail Group are incorporated together and govern BluePeak's subscription to Conga Orchestrate Standard. This Order Form becomes effective on March 15, 2025.

1. Subscription Commitment. Customer is purchasing 80 subscribed workflow seats for an initial two-year committed term ending March 14, 2027.

2. Billing. Supplier will invoice monthly for the committed subscription quantities and any approved overages. Payment is due thirty (30) days from the invoice date.

3. Renewal and Price Adjustment. Upon each annual renewal, the subscription charges will be subject to a 3% annual uplift. Supplier must provide 30 days notice before the applicable renewal date in order to implement the 3% annual uplift for the next renewal term.

4. Precedence. If there is a conflict between this Order Form and the Master Subscription Agreement, this Order Form governs solely with respect to pricing, quantities, and service-specific commercial terms.$ctr1003$
    ),
    (
        'ctr-1004',
        'acc-1004',
        'Conga Quote to Cash Advanced',
        DATE '2025-01-01',
        DATE '2027-12-31',
        160.00,
        'USD',
        600,
        $ctr1004$MASTER SUBSCRIPTION AGREEMENT

This Master Subscription Agreement is entered into between Conga Software, Inc. and Summit Distribution Group for use of Conga Quote to Cash Advanced and related support services.

1. Subscription Term and Renewal. The initial committed term begins on January 1, 2025 and continues through December 31, 2025. Thereafter, the subscription renews automatically for successive one-year terms unless either party provides timely notice of non-renewal.

2. Fees and Invoicing. Customer will be invoiced monthly for 600 subscribed units. Undisputed invoices are due net thirty (30) days from receipt.

3. Renewal Pricing Adjustment. Beginning with the first renewal term, recurring subscription fees are subject to a 4% annual price increase. Supplier may implement the 4% annual price increase by providing Customer at least 30 days notice before the applicable renewal anniversary.

4. General Terms. Order forms and amendments may supersede this agreement solely with respect to pricing, quantities, and renewal mechanics to the extent expressly stated.$ctr1004$
    ),
    (
        'ctr-1005',
        'acc-1005',
        'Conga Lifecycle Cloud',
        DATE '2025-06-25',
        DATE '2027-06-24',
        300.00,
        'USD',
        400,
        $ctr1005$MASTER SUBSCRIPTION AGREEMENT

This Master Subscription Agreement is entered into between Conga Software, Inc. and Redwood BioLabs for access to Conga Lifecycle Cloud.

1. Term. The initial term begins on June 25, 2025 and continues through June 24, 2026. The agreement renews automatically for additional one-year terms unless either party provides notice of non-renewal.

2. Fees and Payment. Customer will be billed monthly for 400 units at the pricing set forth in the applicable ordering document.

3. Renewal Pricing Adjustment. Beginning with the first renewal term, recurring subscription charges are subject to a 2% annual uplift. Supplier may implement the 2% annual uplift with at least 30 days notice before the applicable renewal date.

4. Precedence. Later order forms, renewal schedules, and commercial amendments may supersede this agreement for pricing and renewal mechanics where expressly stated.$ctr1005$
    ),
    (
        'ctr-2001',
        'acc-2001',
        'Conga Revenue Intelligence Suite',
        DATE '2025-04-01',
        DATE '2027-03-31',
        200.00,
        'USD',
        500,
        $ctr2001$MASTER SUBSCRIPTION AGREEMENT

This Master Subscription Agreement ("Agreement") is entered into as of April 1, 2025, by and between Conga Software, Inc. ("Supplier") and Pinnacle Logistics Corp. ("Customer"). This Agreement governs Customer's subscription to Conga Revenue Intelligence Suite.

1. Subscription Term and Renewal. The initial subscription term commences on April 1, 2025 and continues through March 31, 2026. Thereafter, the subscription renews automatically for successive twelve-month terms unless either party provides written notice of non-renewal at least 30 days before the renewal date.

2. Fees and Invoicing. Customer will be invoiced monthly for 500 subscribed platform seats at $200.00 per seat per month. Undisputed invoices are due net thirty (30) days from receipt.

3. Renewal Pricing Adjustment. Beginning with the first renewal term and on each renewal anniversary thereafter, the subscription fees are subject to a 3% annual price increase. Supplier may implement the 3% annual price increase by providing Customer at least 30 days notice prior to the applicable renewal anniversary.

4. Precedence. Order forms, amendments, and renewal schedules executed after the effective date of this Agreement may supersede the commercial terms herein to the extent expressly stated therein.

5. General Terms. This Agreement, together with any order forms and amendments, constitutes the entire agreement between the parties.$ctr2001$
    )
ON CONFLICT (contract_id) DO UPDATE SET
    account_id = EXCLUDED.account_id,
    product_name = EXCLUDED.product_name,
    term_start = EXCLUDED.term_start,
    term_end = EXCLUDED.term_end,
    base_price = EXCLUDED.base_price,
    currency = EXCLUDED.currency,
    quantity = EXCLUDED.quantity,
    raw_contract_text = EXCLUDED.raw_contract_text;

INSERT INTO contract_documents (
    document_id,
    contract_id,
    document_type,
    file_name,
    mime_type,
    storage_key,
    version,
    page_count,
    ingestion_status
)
VALUES
    (
        'doc-1001',
        'ctr-1001',
        'msa',
        'northwind-master-subscription-agreement-v1.pdf',
        'application/pdf',
        'contracts/acc-1001/ctr-1001/msa-v1.pdf',
        1,
        4,
        'pending_upload'
    ),
    (
        'doc-1002',
        'ctr-1002',
        'msa',
        'apex-software-subscription-agreement-v1.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1002/ctr-1002/msa-v1.docx',
        1,
        3,
        'pending_upload'
    ),
    (
        'doc-1003',
        'ctr-1003',
        'order_form',
        'bluepeak-order-form-v1.pdf',
        'application/pdf',
        'contracts/acc-1003/ctr-1003/order-form-v1.pdf',
        1,
        2,
        'pending_upload'
    ),
    (
        'doc-1101',
        'ctr-1001',
        'order_form',
        'northwind-enterprise-order-form-v2.pdf',
        'application/pdf',
        'contracts/acc-1001/ctr-1001/order-form-v2.pdf',
        2,
        2,
        'pending_upload'
    ),
    (
        'doc-1102',
        'ctr-1001',
        'amendment',
        'northwind-commercial-amendment-v1.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1001/ctr-1001/amendment-v1.docx',
        1,
        3,
        'pending_upload'
    ),
    (
        'doc-1103',
        'ctr-1001',
        'amendment',
        'northwind-commercial-amendment-v2.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1001/ctr-1001/amendment-v2.docx',
        2,
        3,
        'pending_upload'
    ),
    (
        'doc-1104',
        'ctr-1001',
        'renewal_notice',
        'northwind-renewal-pricing-memo-v1.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1001/ctr-1001/renewal-memo-v1.docx',
        1,
        2,
        'pending_upload'
    ),
    (
        'doc-1201',
        'ctr-1002',
        'amendment',
        'apex-pricing-amendment-v1.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1002/ctr-1002/amendment-v1.docx',
        1,
        2,
        'pending_upload'
    ),
    (
        'doc-1202',
        'ctr-1002',
        'order_form',
        'apex-renewal-schedule-v2.pdf',
        'application/pdf',
        'contracts/acc-1002/ctr-1002/renewal-schedule-v2.pdf',
        2,
        2,
        'pending_upload'
    ),
    (
        'doc-1203',
        'ctr-1002',
        'renewal_notice',
        'apex-renewal-notice-draft-v1.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1002/ctr-1002/renewal-notice-draft-v1.docx',
        1,
        2,
        'pending_upload'
    ),
    (
        'doc-1401',
        'ctr-1004',
        'msa',
        'summit-master-subscription-agreement-v1.pdf',
        'application/pdf',
        'contracts/acc-1004/ctr-1004/msa-v1.pdf',
        1,
        4,
        'pending_upload'
    ),
    (
        'doc-1402',
        'ctr-1004',
        'order_form',
        'summit-order-form-v2.pdf',
        'application/pdf',
        'contracts/acc-1004/ctr-1004/order-form-v2.pdf',
        2,
        2,
        'pending_upload'
    ),
    (
        'doc-1403',
        'ctr-1004',
        'amendment',
        'summit-commercial-amendment-v3.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1004/ctr-1004/amendment-v3.docx',
        3,
        3,
        'pending_upload'
    ),
    (
        'doc-1404',
        'ctr-1004',
        'renewal_notice',
        'summit-renewal-operations-brief-v1.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1004/ctr-1004/renewal-brief-v1.docx',
        1,
        2,
        'pending_upload'
    ),
    (
        'doc-1501',
        'ctr-1005',
        'msa',
        'redwood-master-subscription-agreement-v1.pdf',
        'application/pdf',
        'contracts/acc-1005/ctr-1005/msa-v1.pdf',
        1,
        4,
        'pending_upload'
    ),
    (
        'doc-1502',
        'ctr-1005',
        'order_form',
        'redwood-renewal-schedule-v2.pdf',
        'application/pdf',
        'contracts/acc-1005/ctr-1005/renewal-schedule-v2.pdf',
        2,
        2,
        'pending_upload'
    ),
    (
        'doc-1503',
        'ctr-1005',
        'amendment',
        'redwood-commercial-amendment-v1.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1005/ctr-1005/amendment-v1.docx',
        1,
        2,
        'pending_upload'
    ),
    (
        'doc-1504',
        'ctr-1005',
        'renewal_notice',
        'redwood-renewal-playbook-v1.docx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'contracts/acc-1005/ctr-1005/renewal-playbook-v1.docx',
        1,
        2,
        'pending_upload'
    )
ON CONFLICT (document_id) DO UPDATE SET
    contract_id = EXCLUDED.contract_id,
    document_type = EXCLUDED.document_type,
    file_name = EXCLUDED.file_name,
    mime_type = EXCLUDED.mime_type,
    storage_key = EXCLUDED.storage_key,
    version = EXCLUDED.version,
    page_count = EXCLUDED.page_count;

INSERT INTO invoice_lines (
    invoice_id,
    account_id,
    contract_id,
    billing_period_start,
    billing_period_end,
    amount_billed,
    quantity
)
VALUES
    ('inv-1001', 'acc-1001', 'ctr-1001', DATE '2025-12-01', DATE '2025-12-31', 100000.00, 1000),
    ('inv-1002', 'acc-1001', 'ctr-1001', DATE '2026-01-01', DATE '2026-01-31', 100000.00, 1000),
    ('inv-1003', 'acc-1001', 'ctr-1001', DATE '2026-02-01', DATE '2026-02-28', 100000.00, 1000),
    ('inv-1004', 'acc-1001', 'ctr-1001', DATE '2026-03-01', DATE '2026-03-31', 100000.00, 1000),
    ('inv-2001', 'acc-1002', 'ctr-1002', DATE '2026-04-01', DATE '2026-04-30', 37500.00, 150),
    ('inv-3001', 'acc-1003', 'ctr-1003', DATE '2026-03-15', DATE '2026-04-14', 14832.00, 80),
    ('inv-4000', 'acc-1004', 'ctr-1004', DATE '2025-12-01', DATE '2025-12-31', 96000.00, 600),
    ('inv-4001', 'acc-1004', 'ctr-1004', DATE '2026-01-01', DATE '2026-01-31', 96000.00, 600),
    ('inv-4002', 'acc-1004', 'ctr-1004', DATE '2026-02-01', DATE '2026-02-28', 96000.00, 600),
    ('inv-4003', 'acc-1004', 'ctr-1004', DATE '2026-03-01', DATE '2026-03-31', 96000.00, 600),
    ('inv-4004', 'acc-1004', 'ctr-1004', DATE '2026-04-01', DATE '2026-04-30', 96000.00, 600),
    ('inv-5001', 'acc-1005', 'ctr-1005', DATE '2026-04-01', DATE '2026-04-30', 120000.00, 400),
    ('inv-6001', 'acc-2001', 'ctr-2001', DATE '2026-03-01', DATE '2026-03-31', 100000.00, 500),
    ('inv-6002', 'acc-2001', 'ctr-2001', DATE '2026-04-01', DATE '2026-04-30', 100000.00, 500),
    ('inv-6003', 'acc-2001', 'ctr-2001', DATE '2026-05-01', DATE '2026-05-31', 100000.00, 500)
ON CONFLICT (invoice_id) DO UPDATE SET
    account_id = EXCLUDED.account_id,
    contract_id = EXCLUDED.contract_id,
    billing_period_start = EXCLUDED.billing_period_start,
    billing_period_end = EXCLUDED.billing_period_end,
    amount_billed = EXCLUDED.amount_billed,
    quantity = EXCLUDED.quantity;

INSERT INTO renewal_events (contract_id, event_type, event_date)
VALUES
    ('ctr-1003', 'notice_sent', DATE '2026-02-10')
ON CONFLICT (contract_id, event_type, event_date) DO NOTHING;

INSERT INTO obligation_extractions (
    extraction_id,
    contract_id,
    document_id,
    obligation_type,
    value,
    effective_date,
    notice_window_days,
    source_clause_text,
    page_number,
    confidence_score,
    extraction_method
)
VALUES
    ('ext-1001', 'ctr-1001', 'doc-1001', 'annual_uplift', 5.00, DATE '2026-01-01', 30, 'Beginning with the first renewal term and on each subsequent renewal anniversary, the subscription fees are subject to a 5% annual price increase. Supplier may implement the 5% annual price increase by providing Customer at least 30 days notice prior to the applicable renewal anniversary.', 2, 0.75, 'ai-pdf-native-text'),
    ('ext-1101', 'ctr-1001', 'doc-1101', 'annual_uplift', 6.00, DATE '2026-01-01', 30, 'For commercial pricing only, this order form supersedes the master agreement and sets the first renewal uplift at 6% of recurring subscription charges. Supplier may implement the 6% annual uplift for the next renewal term by providing Customer at least 30 days notice before the applicable renewal anniversary.', 2, 0.81, 'ai-pdf-native-text'),
    ('ext-1102', 'ctr-1001', 'doc-1102', 'annual_uplift', 7.00, DATE '2026-01-01', 45, 'Effective for the 2026 renewal planning cycle, the parties amend the renewal pricing clause to permit a 7% annual uplift. Supplier may apply the 7% annual uplift upon providing Customer at least 45 days notice before the relevant renewal date.', 2, 0.85, 'ai-docx-native-text'),
    ('ext-1103', 'ctr-1001', 'doc-1103', 'annual_uplift', 9.00, DATE '2026-01-01', 60, 'The parties agree that, beginning with the next renewal term, subscription fees are subject to a 9% annual price increase. Supplier may implement the 9% annual price increase by providing Customer at least 60 days notice before the applicable renewal anniversary.', 2, 0.95, 'ai-docx-native-text'),
    ('ext-1104', 'ctr-1001', 'doc-1104', 'annual_uplift', 9.00, DATE '2026-01-01', 60, 'The renewal team prepared a customer-facing pricing memo confirming the commercial amendment target of a 9% annual uplift for the 2026 renewal cycle. The memo states that 60 days notice is required before the renewal anniversary for the 9% uplift to take effect.', 1, 0.90, 'ai-docx-native-text'),
    ('ext-2001', 'ctr-1002', 'doc-1002', 'annual_uplift', 5.00, DATE '2026-06-01', 30, 'Commencing on the first renewal date and each renewal term thereafter, the recurring subscription charges will include a 5% annual uplift. Supplier may apply the 5% annual uplift provided Supplier gives Customer no less than 30 days notice before the renewal date.', 2, 0.77, 'ai-docx-native-text'),
    ('ext-1201', 'ctr-1002', 'doc-1201', 'annual_uplift', 4.00, DATE '2026-06-01', 21, 'This pricing amendment updates the Apex commercial package to a 4% annual uplift for the next renewal term. The 4% uplift may be implemented if Supplier delivers no less than 21 days notice before renewal.', 1, 0.81, 'ai-docx-native-text'),
    ('ext-1202', 'ctr-1002', 'doc-1202', 'annual_uplift', 6.00, DATE '2026-06-01', 14, 'The most recent renewal schedule supersedes prior pricing amendments and sets the 2026 renewal uplift at 6% of recurring subscription fees. Supplier must send the formal renewal notice at least 14 days before June 1, 2026 in order to implement the 6% uplift.', 2, 0.94, 'ai-pdf-native-text'),
    ('ext-1203', 'ctr-1002', 'doc-1203', 'annual_uplift', 6.00, DATE '2026-06-01', 14, 'This draft renewal notice references a 6% annual uplift and a final outbound notice deadline of May 18, 2026. The document was prepared internally and does not itself confirm that notice has been sent.', 1, 0.89, 'ai-docx-native-text'),
    ('ext-3001', 'ctr-1003', 'doc-1003', 'annual_uplift', 3.00, DATE '2026-03-15', 30, 'Upon each annual renewal, the subscription charges will be subject to a 3% annual uplift. Supplier must provide 30 days notice before the applicable renewal date in order to implement the 3% annual uplift for the next renewal term.', 2, 0.90, 'ai-pdf-native-text'),
    ('ext-1401', 'ctr-1004', 'doc-1401', 'annual_uplift', 4.00, DATE '2026-01-01', 30, 'Beginning with the first renewal term, recurring subscription fees are subject to a 4% annual price increase. Supplier may implement the 4% annual price increase by providing Customer at least 30 days notice before the applicable renewal anniversary.', 2, 0.78, 'ai-pdf-native-text'),
    ('ext-1402', 'ctr-1004', 'doc-1402', 'annual_uplift', 6.00, DATE '2026-01-01', 30, 'For Conga Quote to Cash Advanced, the executed order form overrides the master agreement pricing mechanics and sets a 6% annual uplift at renewal. Supplier may apply the 6% uplift by providing Customer at least 30 days notice before the renewal anniversary.', 2, 0.84, 'ai-pdf-native-text'),
    ('ext-1403', 'ctr-1004', 'doc-1403', 'annual_uplift', 8.00, DATE '2026-01-01', 60, 'The parties later executed a commercial amendment providing that recurring subscription charges are subject to an 8% annual uplift beginning January 1, 2026. Supplier may implement the 8% annual uplift upon providing Customer at least 60 days notice before the applicable renewal anniversary.', 2, 0.96, 'ai-docx-native-text'),
    ('ext-1404', 'ctr-1004', 'doc-1404', 'annual_uplift', 8.00, DATE '2026-01-01', 60, 'Revenue operations documented the 2026 renewal assumption as an 8% annual uplift with a 60 day notice requirement. The brief references the controlling commercial amendment as the source of record for pricing changes.', 1, 0.91, 'ai-docx-native-text'),
    ('ext-1501', 'ctr-1005', 'doc-1501', 'annual_uplift', 2.00, DATE '2026-06-25', 30, 'Beginning with the first renewal term, recurring subscription charges are subject to a 2% annual uplift. Supplier may implement the 2% annual uplift with at least 30 days notice before the applicable renewal date.', 2, 0.76, 'ai-pdf-native-text'),
    ('ext-1502', 'ctr-1005', 'doc-1502', 'annual_uplift', 4.00, DATE '2026-06-25', 21, 'The Redwood renewal schedule increases the upcoming renewal uplift from the base agreement level to 4% of recurring subscription fees. Supplier must provide at least 21 days notice before the renewal date to apply the 4% uplift.', 2, 0.82, 'ai-pdf-native-text'),
    ('ext-1503', 'ctr-1005', 'doc-1503', 'annual_uplift', 5.00, DATE '2026-06-25', 30, 'The later Redwood commercial amendment sets the next renewal uplift at 5% and supersedes any inconsistent 2% or 4% pricing references. Supplier may implement the 5% uplift with at least 30 days notice before June 25, 2026.', 1, 0.95, 'ai-docx-native-text'),
    ('ext-1504', 'ctr-1005', 'doc-1504', 'annual_uplift', 5.00, DATE '2026-06-25', 30, 'The renewal playbook confirms the operational target of a 5% annual uplift and identifies May 26, 2026 as the outbound notice deadline. The document is an internal planning artifact and does not confirm that notice has yet been sent.', 1, 0.89, 'ai-docx-native-text')
ON CONFLICT (extraction_id) DO UPDATE SET
    contract_id = EXCLUDED.contract_id,
    document_id = EXCLUDED.document_id,
    obligation_type = EXCLUDED.obligation_type,
    value = EXCLUDED.value,
    effective_date = EXCLUDED.effective_date,
    notice_window_days = EXCLUDED.notice_window_days,
    source_clause_text = EXCLUDED.source_clause_text,
    page_number = EXCLUDED.page_number,
    confidence_score = EXCLUDED.confidence_score,
    extraction_method = EXCLUDED.extraction_method;