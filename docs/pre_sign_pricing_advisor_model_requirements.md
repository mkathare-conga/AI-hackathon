# Pre-Sign Pricing Advisor

## Brief Description

Pre-Sign Pricing Advisor is a negotiation-support agent that helps the seller decide whether the final paper can carry stronger pricing before signature. It uses prior deals with the same customer account to recommend a better unit price, estimate the close-confidence tradeoff, show the pricing floor, and highlight the approval and signing considerations that matter before the document is signed.

## Product Output Requirements

For each live opportunity, the agent should return:

- current unit price and current discount from list
- recommended improved unit price and recommended discount
- minimum acceptable pricing floor
- current annual contract value and recommended annual contract value
- incremental annual contract value and total contract value impact
- deal closing confidence at current price
- deal closing confidence at improved price
- same-company win rate and training sample size
- closest historical comparables from the same company
- approval path and signing considerations
- recommended actions for the account executive or deal desk

## ML Model Requirements

### Problem Framing

- Primary task: predict probability of closing at a candidate price point.
- Secondary task: recommend the highest safe price that preserves acceptable close confidence.
- Unit of prediction: one deal version or one final-offer scenario for a specific opportunity.

### Labels

- `won_or_lost`: binary label for whether the deal closed.
- `signed_unit_price`: final realized unit price.
- `time_to_close_days`: optional regression target for cycle-time sensitivity.
- `discount_approved`: optional classification target for approval likelihood.

### Feature Requirements

- Account identity and parent-company rollup.
- Product family and SKU mix.
- List price, offered price, effective discount, quantity, and term length.
- Support tier, services bundle, implementation scope, and strategic flag.
- Procurement rigor, legal complexity, competitor presence, and stage.
- Historical same-company price bands and same-company win rates.
- Previous closed-won and closed-lost outcomes for the same company.
- Seasonality and quarter-end timing features.
- Rep, region, segment, and industry features if available.

### Recommended Model Stack

- Baseline: logistic regression on normalized deal features.
- Strong tabular model: gradient boosted trees such as XGBoost, LightGBM, or CatBoost.
- Ranking layer: optional price-search step that evaluates candidate prices and selects the highest one above a close-confidence floor.
- Calibration: Platt scaling or isotonic regression so confidence scores are usable by sellers.

### Training Requirements

- Train only on prior closed opportunities; do not leak future outcomes into the feature set.
- Split train/validation/test chronologically, not randomly.
- Build a same-company subset first; back off to parent-company, industry, or segment peers only when same-company history is sparse.
- Retrain regularly as new closed deals arrive.
- Track feature drift, calibration drift, and win-rate drift over time.

### Evaluation Requirements

- Classification quality: ROC-AUC, PR-AUC, log loss, Brier score.
- Calibration quality: reliability curve and expected calibration error.
- Business quality: uplift in retained price, total ACV increase, and win-rate preservation compared with current pricing behavior.
- Recommendation quality: percentage of suggestions that would have improved ACV without dropping below the chosen confidence floor.

### Governance Requirements

- Explainability for sellers: top contributing features, comparable deals, and price-band rationale.
- Human-in-the-loop controls: the model recommends, humans approve.
- Guardrails for floors and ceilings by segment, product, and approval policy.
- Bias review across segment, region, and rep cohorts.
- Clear audit trail of model version, training cutoff date, and features used for each recommendation.

## Dummy Data Needed To Build And Train It

### Historical Deal Dataset

Each row should represent one completed deal version for the same company:

- `deal_id`
- `account_name`
- `parent_account_name` optionally
- `product_name`
- `outcome` as won or lost
- `list_unit_price`
- `final_unit_price`
- `quantity`
- `term_months`
- `support_tier`
- `procurement_rigor`
- `strategic`
- `signed_date`
- `competitor`
- `notes`

### Open Opportunity Dataset

Each row should represent a current deal being evaluated before signature:

- `opportunity_id`
- `account_name`
- `opportunity_name`
- `product_name`
- `stage`
- `list_unit_price`
- `current_unit_price`
- `quantity`
- `term_months`
- `support_tier`
- `procurement_rigor`
- `strategic`
- `currency`
- `close_target_date`

### Optional Enrichment Datasets

- product price book and floor rules
- approval policy thresholds
- competitor matrix
- rep and region metadata
- procurement and legal cycle benchmarks

## Dummy Data Added In This Repo

The demo implementation uses these synthetic files:

- [data/synthetic/pricing_recommendation/historical_deals.json](data/synthetic/pricing_recommendation/historical_deals.json)
- [data/synthetic/pricing_recommendation/open_opportunities.json](data/synthetic/pricing_recommendation/open_opportunities.json)

These files provide same-company closed-won and closed-lost examples for four accounts plus four open opportunities that the new agent scores in the UI.