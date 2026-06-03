-- Seed data for Quote-to-Contract Drift Detector demo

INSERT INTO quotes (quote_id, account_name, opportunity_name, created_date, status)
VALUES
    ('quote-2001', 'TechVault Solutions', 'TechVault CLM Expansion', '2025-09-15', 'approved'),
    ('quote-2002', 'Meridian Healthcare', 'Meridian Enterprise Renewal', '2025-10-01', 'approved'),
    ('quote-2003', 'Atlas Manufacturing', 'Atlas Digital Transformation', '2025-11-10', 'approved')
ON CONFLICT (quote_id) DO NOTHING;

INSERT INTO quote_lines (line_id, quote_id, product_name, quantity, unit_price, discount_percent, support_tier, renewal_uplift_percent, payment_terms_days, currency)
VALUES
    -- TechVault: 3 line items
    ('ql-2001-1', 'quote-2001', 'Conga CLM Enterprise', 1000, 120.00, 10, 'premium', 5.0, 30, 'USD'),
    ('ql-2001-2', 'quote-2001', 'Conga Sign Advanced', 500, 45.00, 5, 'standard', 3.0, 30, 'USD'),
    ('ql-2001-3', 'quote-2001', 'Implementation Services', 1, 75000.00, 0, 'premium', NULL, 30, 'USD'),
    -- Meridian: 2 line items
    ('ql-2002-1', 'quote-2002', 'Conga Composer Premium', 2000, 85.00, 15, 'premium', 6.0, 30, 'USD'),
    ('ql-2002-2', 'quote-2002', 'Conga Orchestrate Standard', 500, 60.00, 10, 'standard', 4.0, 30, 'USD'),
    -- Atlas: 2 line items
    ('ql-2003-1', 'quote-2003', 'Conga Revenue Intelligence', 800, 200.00, 12, 'premium', 5.0, 45, 'USD'),
    ('ql-2003-2', 'quote-2003', 'Conga Analytics Suite', 800, 75.00, 8, 'standard', 3.0, 45, 'USD')
ON CONFLICT (line_id) DO NOTHING;

INSERT INTO drift_contracts (contract_id, quote_id, contract_text, signed_date)
VALUES
    (
        'drift-ctr-2001',
        'quote-2001',
        $dc2001$MASTER SUBSCRIPTION AGREEMENT

This Master Subscription Agreement ("Agreement") is entered into as of October 15, 2025, by and between Conga Software, Inc. ("Supplier") and TechVault Solutions, Inc. ("Customer").

1. Subscription Scope. Supplier grants Customer a non-exclusive license to access and use the following services during the Subscription Term:
   (a) Conga CLM Enterprise — 900 named-user seats
   (b) Conga Sign Advanced — 500 named-user seats

2. Subscription Term. The initial term commences on November 1, 2025 and continues through October 31, 2027. The Agreement renews automatically for successive twelve-month terms unless either party provides written notice of non-renewal at least sixty (60) days before the end of the then-current term.

3. Fees and Payment.
   (a) Conga CLM Enterprise: $108.00 per seat per month (reflects 10% volume discount).
   (b) Conga Sign Advanced: $42.75 per seat per month (reflects 5% volume discount).
   (c) All invoices are due net sixty (60) days from the invoice date.

4. Annual Price Adjustment. Beginning on the first anniversary of the Term Start Date and on each subsequent anniversary, the recurring subscription fees shall increase by 3% annually. Supplier must provide at least thirty (30) days written notice before the applicable anniversary.

5. Support Services. Supplier will provide standard support during business hours (8am-6pm ET, Monday through Friday). Premium support with 24/7 coverage and dedicated account management is available as a separate add-on at published rates.

6. Implementation. Customer acknowledges that implementation services described in the original proposal are not included in this Agreement and must be purchased separately under a Statement of Work.

7. Limitation of Liability. Supplier's aggregate liability shall not exceed the fees paid by Customer during the twelve months preceding the claim.

8. Governing Law. This Agreement shall be governed by the laws of the State of Delaware.$dc2001$,
        DATE '2025-10-15'
    ),
    (
        'drift-ctr-2002',
        'quote-2002',
        $dc2002$SOFTWARE SUBSCRIPTION AGREEMENT

Effective Date: November 1, 2025
Parties: Conga Software, Inc. ("Supplier") and Meridian Healthcare Group ("Customer")

ARTICLE 1 — SUBSCRIPTION SERVICES

1.1 Licensed Products.
   - Conga Composer Premium: 1,800 named-user subscriptions
   - Conga Orchestrate Standard: 500 workflow subscriptions

1.2 Term. Initial term of twenty-four (24) months commencing November 1, 2025 through October 31, 2027. Auto-renews for successive one-year terms unless either party provides ninety (90) days written notice of non-renewal.

ARTICLE 2 — COMMERCIAL TERMS

2.1 Pricing.
   - Conga Composer Premium: $72.25 per user per month (15% discount applied)
   - Conga Orchestrate Standard: $54.00 per subscription per month (10% discount applied)

2.2 Payment. All invoices are payable net ninety (90) days from the date of invoice. Late payments shall bear interest at 1.5% per month.

2.3 Annual Adjustment. On each anniversary of the Effective Date, recurring subscription charges will be subject to a maximum increase of 2% per annum. This cap applies regardless of any other pricing language in prior proposals or quotes.

ARTICLE 3 — SUPPORT AND SERVICES

3.1 Support Level. Supplier will provide standard business-hours support for all licensed products. Premium support coverage referenced in the sales proposal is not included unless separately contracted.

3.2 Service Level. Supplier commits to 99.5% monthly uptime measured at the application tier.

ARTICLE 4 — GENERAL PROVISIONS

4.1 Entire Agreement. This Agreement constitutes the entire agreement and supersedes all prior negotiations, proposals, and communications.$dc2002$,
        DATE '2025-11-01'
    ),
    (
        'drift-ctr-2003',
        'quote-2003',
        $dc2003$ENTERPRISE SUBSCRIPTION AND SERVICES AGREEMENT

Date: December 1, 2025
Between: Conga Software, Inc. and Atlas Manufacturing Corp.

SECTION 1 — SUBSCRIPTIONS

1.1 Products and Quantities.
   Customer subscribes to the following:
   - Conga Revenue Intelligence: 800 seats at $176.00 per seat per month (12% discount)
   - Conga Analytics Suite: 600 seats at $69.00 per seat per month (8% discount)

1.2 Subscription Period. Three (3) years commencing January 1, 2026 through December 31, 2028.

SECTION 2 — FINANCIAL TERMS

2.1 Payment Schedule. All amounts are due net thirty (30) days from invoice date.

2.2 Annual Escalation. Subscription fees will increase by 5% on each anniversary of the Subscription Start Date. Supplier shall provide no less than thirty (30) days written notice.

2.3 Discount Protection. The volume discounts set forth in Section 1.1 are fixed for the initial three-year term and shall not be recalculated unless Customer increases seat count by more than 20%.

SECTION 3 — SUPPORT

3.1 Included Support. All subscriptions include standard business-hours support.

3.2 Premium Upgrade. Customer may upgrade Conga Revenue Intelligence support to premium tier at an additional $15 per seat per month. This upgrade is optional and not included in base pricing.

SECTION 4 — PROFESSIONAL SERVICES

4.1 Not Included. No professional services, implementation, training, or onboarding are included in this Agreement unless separately documented in a Statement of Work.

SECTION 5 — GENERAL

5.1 Governing Law. State of New York.
5.2 Entire Agreement. This Agreement supersedes all prior proposals and communications.$dc2003$,
        DATE '2025-12-01'
    )
ON CONFLICT (contract_id) DO NOTHING;
