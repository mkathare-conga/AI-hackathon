# Conga AI Hackathon — Idea Brainstorming Document

## Context
- **Company**: Conga (Revenue Lifecycle Management)
- **Hackathon Categories**: Product, Engineering, AI with Enterprise Apps, AI in Client Onboarding & Implementation
- **Team**: Engineering
- **Constraint**: Must use synthetic data (no access to real Conga customer data)
- **Constraint**: Must be genuinely AI-first (not just CRUD with an AI label)
- **Constraint**: Must not overlap with features Conga is already building

---

## Conga Product Portfolio

| Product | Purpose |
|---------|---------|
| Conga CLM | Contract Lifecycle Management (creation → signature → renewal) |
| Conga CPQ | Configure, Price, Quote |
| Conga Composer | Document generation/automation (templates + Salesforce merge) |
| Conga Sign | eSignature |
| Conga Grid | Data management within Salesforce |
| Conga Orchestrate | Workflow automation |
| Conga Digital Commerce | eCommerce/order management |

---

## Market Position (2026 SoftwareReviews CLM Rankings)

| Vendor | CX Score | Key AI Differentiator |
|--------|----------|----------------------|
| Malbek | 8.7 | Most intuitive, AI-fueled |
| DocuSign | 8.2 | Iris AI — AI-assisted review, data extractions, AI contract agents |
| Oracle | 8.2 | Cloud procurement automation |
| Agiloft | 8.1 | Astra — real-time contract intelligence, no-code, 80% faster |
| SAP | 8.0 | Business network integration |
| PandaDoc | 7.9 | CRM-native simplicity |
| **Conga CLM** | **7.7** | Limited AI currently |
| Sirion | 7.8 | Smarter Contracting, obligation intelligence |
| Icertis | 7.1 | Vera AI — Composer Agent, Redline Agent, Insights Agent, Knowledge Graph |

---

## Customer Pain Points (from real reviews)

| Category | Pain Point | Severity |
|----------|-----------|----------|
| Complexity | Initial setup/configuration is extremely complex for workflows | HIGH |
| Learning Curve | Steep; requires deep Salesforce data structure knowledge | HIGH |
| Scalability | Too much customization, not easy to scale | HIGH |
| AI Gap | Lacks AI for redlining and identifying terms needing revision | HIGH |
| Integration | Beyond Salesforce requires significant effort; SAP sync issues | MEDIUM |
| Support | Sometimes not very efficient | MEDIUM |
| Pricing | Expensive, non-transparent; add-ons make it pricier | MEDIUM |
| Documentation | Not up to par with Salesforce docs | MEDIUM |
| Template Mgmt | Complex to maintain versions and updates | MEDIUM |
| Debugging | No good debugging tools for templates/workflows | MEDIUM |

---

## Competitor AI Features (What Conga is Missing)

### Icertis (Vera AI Platform)
- **Composer Agent**: Conversational AI → compliant contracts in minutes
- **Redline Agent**: AI auto-redlines based on playbooks; procurement does first-pass
- **Insights Agent**: Plain-language answers from contract portfolio
- **Knowledge Graph**: Entity relationships across contracts
- **A2A Protocol + Omni-LLM support**

### DocuSign (Iris AI)
- **AI-Assisted Review**: Automates enforcement of legal standards
- **AI Data Extractions**: Structured data from unstructured contracts
- **Navigator**: Centralized agreement analytics, renewal management, risk flagging
- **Maestro**: No-code workflow builder
- **AI Contract Agents**: Semi-autonomous (coming soon)

### Agiloft (Astra)
- **Real-time contract intelligence** with zero setup
- **No-code interface** for complex workflows
- **1000+ integrations** via drag-and-drop
- **GenAI** for reaching agreement and accessing contract data

---

## Ideas Already Being Built at Conga (EXCLUDED)

| Idea | Status |
|------|--------|
| Quote Agent | ✅ Already exists / in product landscape |
| Search Agent | ✅ Already exists / in product landscape |
| AI Redline Agent | ✅ Already in development |
| Contract Q&A Agent | ✅ Already exists |
| Clause Risk Scoring | ⚠️ Too close to Redline Agent (risk scoring is a precursor to redlining) |

---

## Product Landscape Primer

This section is here so a reader without Conga context can understand overlap risk.

- **Q&A Agent**: Answers plain-language questions about contracts or the portfolio. If an idea is mostly "ask questions over contract data," it overlaps heavily.
- **Search Agent**: Finds contracts, clauses, or terms quickly. If an idea is mostly retrieval or navigation, it overlaps heavily.
- **Quote Agent**: Helps create/configure quotes. If an idea is mostly quote generation or quote assistance, it overlaps heavily.
- **Redline Agent**: Reviews and rewrites contract language against playbooks. If an idea is mostly clause review, risk scoring, or markup suggestions, it overlaps heavily.

### Plain-Language Business Terms

- **Quote**: The commercial offer the seller sends first, such as price, product, discount, and service terms.
- **Draft contract**: The first contract version the seller sends to the buyer.
- **Buyer redline**: The buyer's edited contract version showing requested changes.
- **Final signed contract**: The version both sides finally agree to and sign.
- **Renewal**: Extending the contract for another term.
- **Uplift**: A planned price increase written into the contract, such as "price goes up 5% next year."
- **Billing / invoice**: What the customer was actually charged.

---

## Canonical Idea Catalog

All candidate ideas below use the same format so they are easy to compare.

### Scoring Method

- **Business Value (1-5)**: How painful and important the problem is
- **AI Need (1-5)**: How essential AI is versus simple rules or workflows
- **Synthetic Data Fit (1-5)**: How believable the demo can be using synthetic data only
- **Build Ease (1-5)**: Higher score means easier to build in a hackathon
- **Overlap Safety (1-5)**: Higher score means less overlap with existing or in-progress agents
- **Total Score (/25)**: Sum of the five dimensions above

### Recommended Candidates

#### 1. Revenue Leakage Investigator
- **Merged earlier ideas**: Revenue Operations Intelligence, Contract Obligation Auto-Tracker, Missed Renewal/Uplift Finder
- **Possible sub-agents inside this broader idea**:
	- Contract Obligation Auto-Tracker
	- Missed Renewal/Uplift Finder
	- Quote-to-Contract Drift Detector
	- Billing-vs-Contract Mismatch Finder
- **How Contract Obligation Auto-Tracker fits inside this idea**: It is the part that reads signed contracts, extracts obligations such as renewal notice, price uplift rights, service commitments, and deadlines, and checks whether the business actually acted on them.
- **Problem it is trying to solve**: Revenue leaks out when the commercial terms sold, signed, fulfilled, renewed, and billed drift apart across the revenue lifecycle.
- **Example**: A seller offers a customer software at $100 per user this year and states the price should increase by 5% at renewal. The contract is signed, but next year's invoices still charge $100. The company loses money because nobody caught the missed increase.
- **How AI is used**: Extract rights and obligations from contracts and amendments, reconcile them against quotes, orders, and invoices, explain mismatches, and prioritize findings by likely dollar impact.
- **Can it be done with synthetic data alone?**: Yes. Synthetic quotes, contracts, amendments, invoices, and renewals are very feasible to generate.
- **Build difficulty**: Medium. The full vision is broad, but a first hackathon version can focus on one sub-agent like Missed Renewal/Uplift Finder.
- **Similarity to existing agents/features**: Low overlap. It is not primarily a Q&A, search, quote-generation, or redline product.
- **Current verdict**: Strong candidate
- **Score**: Business Value 5 + AI Need 5 + Synthetic Data Fit 5 + Build Ease 3 + Overlap Safety 5 = **23/25**

#### 2. Quote-to-Contract Drift Detector
- **Merged earlier ideas**: Quote-to-Contract Leakage, part of Revenue Leakage Investigator
- **Problem it is trying to solve**: The deal approved by sales and the contract signed by legal do not match, which creates revenue leakage and downstream confusion.
- **Example**: Sales promised 1,000 licenses, onboarding help, and a 5% annual price increase. The final signed contract quietly changes that to 900 licenses, removes onboarding, and caps the increase at 2%. The business may deliver the wrong thing or charge too little.
- **How AI is used**: Match structured quote lines to unstructured contract terms, detect semantic drift in pricing and obligations, and explain business impact in plain language.
- **Can it be done with synthetic data alone?**: Yes. Synthetic quotes, contracts, and seeded mismatches are straightforward to generate.
- **Build difficulty**: Medium.
- **Similarity to existing agents/features**: Low to Medium overlap. It touches quote and contract data, but it is not mainly a quote-generation agent or a redlining agent.
- **Current verdict**: Strong candidate
- **Score**: 5 + 4 + 5 + 4 + 4 = **22/25**

#### 3. Missed Renewal/Uplift Finder
- **Merged earlier ideas**: Narrow wedge inside Revenue Leakage Investigator
- **Problem it is trying to solve**: Companies sign contracts with renewal dates, notice periods, and annual uplift rights, but teams fail to act on them and leave money on the table.
- **Example**: A contract says the seller can raise price by 5% every year if they give 30 days' notice. Three years pass, the invoices never change, and the seller misses revenue that was already allowed in the signed contract.
- **How AI is used**: Read contract language and amendments, normalize renewal/uplift terms, compare them to invoice history, and explain missed revenue opportunities.
- **Can it be done with synthetic data alone?**: Yes. This is one of the easiest contract-AI ideas to simulate with synthetic data.
- **Build difficulty**: Low to Medium.
- **Similarity to existing agents/features**: Low overlap. It is not primarily Q&A, search, quote creation, or redlining.
- **Current verdict**: Strong candidate and strong first sub-agent
- **Score**: 5 + 5 + 5 + 4 + 5 = **24/25**

#### 4. AI Workflow Reliability Engineer
- **Merged earlier ideas**: AI Workflow Debugger/Optimizer, Deal Cycle Time Bottleneck Analyzer
- **Problem it is trying to solve**: Workflow owners can build and run approval flows, but they cannot easily see why those workflows are slow, brittle, or failing.
- **Example**: An approval flow that used to finish in 2 days now takes 7 days because finance approvals serialize in APAC and one integration retry loop creates queue buildup.
- **How AI is used**: Detect anomalies in workflow runs, cluster failure patterns, attribute bottlenecks to specific steps or integrations, and recommend fixes.
- **Can it be done with synthetic data alone?**: Yes. Workflow runs, step timings, approvals, retries, and failures are easy to synthesize credibly.
- **Build difficulty**: Low to Medium.
- **Similarity to existing agents/features**: Low overlap. It is not Q&A, search, quote generation, or redlining.
- **Current verdict**: Strong engineering candidate
- **Score**: 4 + 5 + 5 + 4 + 5 = **23/25**

#### 5. Discount Leakage and Approval Anomaly Analyzer
- **Merged earlier ideas**: Discount anomaly concept from revenue operations analysis
- **Problem it is trying to solve**: Margin leaks out through inconsistent discounts, exception-heavy approvals, and policy bypasses that no one can audit well.
- **Example**: A rep gets a 28% discount approved where similar deals typically receive 12%, and the finance approval step was skipped entirely.
- **How AI is used**: Detect abnormal discount patterns, abnormal approval paths, and outlier deals that deserve investigation.
- **Can it be done with synthetic data alone?**: Yes. Synthetic deals, discount histories, and approval chains are easy to generate.
- **Build difficulty**: Low to Medium.
- **Similarity to existing agents/features**: Low overlap. It is analytics over deal behavior, not a quote generator or Q&A tool.
- **Current verdict**: Good candidate
- **Score**: 4 + 4 + 5 + 4 + 5 = **22/25**

#### 6. Cross-Contract Conflict & Obligation Graph
- **Merged earlier ideas**: Portfolio Anomaly Detection + Conflicts, Contract Portfolio Intelligence
- **Problem it is trying to solve**: Legal and procurement teams cannot easily see hidden conflicts, overlaps, or obligations across a large contract portfolio.
- **Example**: One partner contract grants exclusivity in Germany, while another overlapping reseller agreement grants the same territory to a different partner.
- **How AI is used**: Resolve entities across documents, reason over time-based clauses and amendments, build a graph of relationships, and surface conflicts.
- **Can it be done with synthetic data alone?**: Yes. Synthetic contracts with seeded contradictions and overlaps are feasible.
- **Build difficulty**: Medium.
- **Similarity to existing agents/features**: Medium to High overlap with a portfolio Q&A/search direction. It is more analytical than Q&A, but the boundary is close.
- **Current verdict**: Viable but crowded
- **Score**: 4 + 5 + 5 + 3 + 3 = **20/25**

#### 7. Integration Failure Radar
- **Merged earlier ideas**: Self-Healing Integration Monitor
- **Problem it is trying to solve**: Revenue operations break when Salesforce, CLM, ERP, billing, or fulfillment systems fall out of sync and nobody can see where the chain broke first.
- **Example**: A contract amendment updates CLM, but ERP never receives the change and billing continues using the old term structure.
- **How AI is used**: Correlate cross-system events, infer likely root cause, and explain failure propagation across systems.
- **Can it be done with synthetic data alone?**: Yes, but the event stream needs to be well-designed to look realistic.
- **Build difficulty**: Medium.
- **Similarity to existing agents/features**: Low overlap. This is operational integration intelligence, not search, Q&A, quote generation, or redlining.
- **Current verdict**: Good secondary candidate
- **Score**: 4 + 4 + 4 + 3 + 5 = **20/25**

#### 8. AI Implementation Accelerator
- **Merged earlier ideas**: AI Implementation Accelerator
- **Problem it is trying to solve**: Conga implementations take too long because teams must translate messy source documents and business rules into fields, workflows, and templates.
- **Example**: A team uploads an old contract pack and process notes, and the system proposes field mappings, workflow branches, and template components for a new rollout.
- **How AI is used**: Infer semantic field mappings, detect conditional logic, and infer workflow/configuration structure from unstructured source material.
- **Can it be done with synthetic data alone?**: Partly. It can be simulated, but the output is harder to make feel real without a convincing target configuration model.
- **Build difficulty**: Medium to High.
- **Similarity to existing agents/features**: Low overlap with current agents, but adjacent to onboarding/services work.
- **Current verdict**: Viable but harder to demo
- **Score**: 4 + 5 + 3 + 2 + 5 = **19/25**

#### 9. AI Template QA and Debugger for Composer + CLM Assets
- **Merged earlier ideas**: Template Version Control & Diff Engine, debugging tools for templates/workflows
- **Problem it is trying to solve**: Template logic, merge fields, and document-generation assets fail in hard-to-debug ways, causing delays, wrong language, or broken outputs.
- **Example**: A renewal template works for US customers, but EMEA renewals fail because one fallback clause references a missing field from SAP.
- **How AI is used**: Diagnose failures semantically, trace missing dependencies, detect regression risk, and suggest likely fixes.
- **Can it be done with synthetic data alone?**: Yes. Synthetic templates, fields, sample payloads, and failure cases are feasible.
- **Build difficulty**: Medium.
- **Similarity to existing agents/features**: Low overlap. This is operational QA, not redlining or Q&A.
- **Current verdict**: Good engineering idea if template pain is familiar to the team
- **Score**: 4 + 4 + 5 + 3 + 5 = **21/25**

### Viable but Less Differentiated

#### 10. Contract Language Generation from Business Intent
- **Merged earlier ideas**: Smart Contract Composer (Conversational), Contract Language Generation from Intent
- **Problem it is trying to solve**: Business users know the commercial intent they want, but turning that into compliant legal language is slow and specialist-dependent.
- **Example**: A user asks for a reseller clause for healthcare in Germany with capped liability and local compliance constraints.
- **How AI is used**: Generate draft contract language under policy, style, jurisdiction, and clause-consistency constraints.
- **Can it be done with synthetic data alone?**: Yes. This is easy to simulate with synthetic clause libraries and prompt inputs.
- **Build difficulty**: Low to Medium.
- **Similarity to existing agents/features**: Medium to High overlap with redline/contract-drafting directions, depending on how Conga scopes those agents.
- **Current verdict**: Viable but differentiation risk is high
- **Score**: 3 + 4 + 5 + 4 + 2 = **18/25**

#### 11. Zero-Code Workflow Builder with AI
- **Merged earlier ideas**: Zero-Code Workflow Builder with AI
- **Problem it is trying to solve**: Non-technical teams struggle to translate process descriptions into workflow graphs, rules, and approval paths.
- **Example**: A user says "route discounts over 20% to finance, then legal if non-standard terms are present" and expects a draft workflow.
- **How AI is used**: Convert natural-language process descriptions into workflow structures, rules, and validation suggestions.
- **Can it be done with synthetic data alone?**: Yes.
- **Build difficulty**: Low to Medium.
- **Similarity to existing agents/features**: Low internal overlap, but strong external overlap because competitors already market no-code builders heavily.
- **Current verdict**: Viable but derivative
- **Score**: 3 + 4 + 5 + 4 + 3 = **19/25**

#### 12. Implementation Risk Predictor
- **Merged earlier ideas**: Implementation Risk Predictor
- **Problem it is trying to solve**: Customer onboarding projects slip because data mappings, templates, workflows, and integrations are not ready at the same time.
- **Example**: The system predicts a go-live miss because mapping sign-off is late, test failures are rising, and an integration dependency is unresolved.
- **How AI is used**: Score implementation risk, reason over dependencies, and explain likely causes of delay.
- **Can it be done with synthetic data alone?**: Partly. Synthetic project data is possible, but it is harder to make convincing than commercial or contract data.
- **Build difficulty**: Medium to High.
- **Similarity to existing agents/features**: Low overlap with current agents.
- **Current verdict**: Viable but abstract
- **Score**: 4 + 4 + 3 + 2 + 5 = **18/25**

### Eliminated or Not Recommended

#### 13. Contract Q&A / Portfolio Search Intelligence
- **Merged earlier ideas**: Contract Portfolio Intelligence Dashboard, Contract Q&A Agent
- **Problem it is trying to solve**: Users want to ask questions about their contract portfolio in plain language.
- **Example**: "Show me all contracts renewing in Q3 with price escalators above 4%."
- **How AI is used**: Retrieval, summarization, natural-language answers over contract data.
- **Can it be done with synthetic data alone?**: Yes.
- **Build difficulty**: Low.
- **Similarity to existing agents/features**: Very high overlap with Q&A Agent and Search Agent.
- **Current verdict**: Eliminated due to direct overlap
- **Score**: 3 + 3 + 5 + 5 + 1 = **17/25**

#### 14. Redline-Adjacent Review Tools
- **Merged earlier ideas**: AI-Powered Contract Redline Agent, Clause Risk Scoring + Explainability, Semantic Contract Diff, Draft-vs-Buyer-Redline Drift Detector
- **What Semantic Contract Diff means in simple terms**: It compares two versions of a contract and highlights changes in business meaning, not just changed words.
- **Problem it is trying to solve**: Legal and sales teams want to know when the buyer's edited contract changes the commercial meaning of the original seller draft in an expensive or risky way.
- **Example**: The seller's draft says payment is due in 30 days, price can rise 5% yearly, and liability is capped at fees paid. The buyer redline changes this to 90-day payment, no yearly increase, and a much larger liability cap. The tool highlights which edits materially hurt revenue or increase risk.
- **How AI is used**: Compare seller draft versus buyer redline semantically, detect which edits change price, payment timing, liability, renewal terms, or obligations, and explain which changes matter most.
- **Can it be done with synthetic data alone?**: Yes.
- **Build difficulty**: Low to Medium.
- **Similarity to existing agents/features**: Very high overlap with Redline Agent work already in progress.
- **Current verdict**: Eliminated due to overlap
- **Score**: 5 + 5 + 5 + 4 + 1 = **20/25**

#### 15. CPQ Deal Desk Co-pilot / Deal Risk Predictor
- **Merged earlier ideas**: AI Deal Desk Co-pilot, CPQ Deal Risk Predictor
- **Problem it is trying to solve**: Sales teams want help predicting deal risk and getting better deal desk guidance.
- **Example**: The system predicts a low chance of close because of pricing, product mix, legal terms, and approval complexity.
- **How AI is used**: Risk scoring and recommendation over historical deal behavior.
- **Can it be done with synthetic data alone?**: Weakly. It really wants real historical deal patterns to be credible.
- **Build difficulty**: Medium.
- **Similarity to existing agents/features**: Medium overlap with quote/deal assistance directions.
- **Current verdict**: Not recommended because synthetic-only evidence will feel weak
- **Score**: 4 + 4 + 1 + 3 + 3 = **15/25**

#### 16. Negotiation Simulator / Multi-Language Negotiation Hub
- **Merged earlier ideas**: Contract Negotiation Simulator/Coach, Multi-Language Contract Negotiation Hub
- **Problem it is trying to solve**: Users want help coaching negotiation outcomes or generating multilingual negotiation support.
- **Example**: Simulate a buyer counsel response in French and suggest better fallback positions.
- **How AI is used**: Conversation simulation, translation, negotiation suggestions.
- **Can it be done with synthetic data alone?**: Yes.
- **Build difficulty**: Low.
- **Similarity to existing agents/features**: Low internal overlap, but high external differentiation risk because this feels like a generic LLM demo.
- **Current verdict**: Not recommended because judges may ask "why not ChatGPT?"
- **Score**: 2 + 3 + 5 + 5 + 3 = **18/25**

#### 17. AI Customer Health Scoring
- **Merged earlier ideas**: AI Customer Health Scoring
- **Problem it is trying to solve**: Teams want to predict customer churn or expansion risk from product usage and account behavior.
- **Example**: Usage drops, support tickets rise, and renewal probability falls for a strategic customer.
- **How AI is used**: Health scoring and churn prediction.
- **Can it be done with synthetic data alone?**: Yes.
- **Build difficulty**: Medium.
- **Similarity to existing agents/features**: Low overlap internally, but weak Conga-specific differentiation.
- **Current verdict**: Not recommended because it is too generic for this hackathon
- **Score**: 3 + 4 + 4 + 3 + 4 = **18/25**

---

## Score Summary

| Idea | Verdict | Total Score |
|------|---------|-------------|
| Missed Renewal/Uplift Finder | Strong candidate | **24/25** |
| Revenue Leakage Investigator | Strong candidate | **23/25** |
| AI Workflow Reliability Engineer | Strong engineering candidate | **23/25** |
| Quote-to-Contract Drift Detector | Strong candidate | **22/25** |
| Discount Leakage and Approval Anomaly Analyzer | Good candidate | **22/25** |
| AI Template QA and Debugger | Good engineering idea | **21/25** |
| Cross-Contract Conflict & Obligation Graph | Viable but crowded | **20/25** |
| Integration Failure Radar | Good secondary candidate | **20/25** |
| AI Implementation Accelerator | Viable but harder to demo | **19/25** |
| Zero-Code Workflow Builder with AI | Viable but derivative | **19/25** |
| Contract Language Generation from Business Intent | Viable but differentiation risk | **18/25** |
| Implementation Risk Predictor | Viable but abstract | **18/25** |
| Negotiation Simulator / Multi-Language Negotiation Hub | Not recommended | **18/25** |
| AI Customer Health Scoring | Not recommended | **18/25** |
| Contract Q&A / Portfolio Search Intelligence | Eliminated due to overlap | **17/25** |
| CPQ Deal Desk Co-pilot / Deal Risk Predictor | Not recommended for synthetic-only demo | **15/25** |
| Redline-Adjacent Review Tools | Eliminated due to overlap | **20/25** |

### What This Means

1. The clearest and easiest first wedge is **Missed Renewal/Uplift Finder**.
2. The strongest full-platform story is **Revenue Leakage Investigator**, with **Missed Renewal/Uplift Finder** as the first specialist agent.
3. The strongest pure engineering story is **AI Workflow Reliability Engineer**.
4. The main overlap traps are anything centered on **Q&A/search** or **redlining/review**.
5. The main synthetic-data trap is anything that depends on real historical win/loss or customer-behavior data.

---

## Current Recommendation

### Best Overall Story

#### Revenue Leakage Investigator with Missed Renewal/Uplift Finder as the First Agent
- **Why it stands out**: Strong Conga fit, strong ROI story, low overlap with existing agent work, and a believable synthetic-data demo.

### Best Backup

#### Quote-to-Contract Drift Detector
- **Why it stands out**: Very easy to explain and highly aligned to Conga's CPQ + CLM story.

### Best Engineering-Only Option

#### AI Workflow Reliability Engineer
- **Why it stands out**: Strong engineering category story and easiest operational dataset to synthesize.

---

*Document updated: April 30, 2026*
