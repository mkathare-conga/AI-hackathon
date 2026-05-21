# Commercial Execution Intelligence Platform Presentation

This file is a slide-by-slide presentation outline for the hackathon demo.

## Slide 1: Title

### Slide title

Commercial Execution Intelligence Platform

### Subtitle

Revenue Leakage Investigator is the first live agent

### On-slide points

- AI-assisted platform for post-signature commercial execution
- Shared evidence layer across contracts, amendments, invoices, and renewals
- First live agent: Revenue Leakage Investigator

### Visual suggestion

- Product UI hero screenshot
- Small callout that highlights `Active agent · Revenue Leakage Investigator`

---

## Slide 2: The Problem

### Slide title

The contract is signed, but revenue execution drifts

### On-slide points

- Pricing rights are defined in contracts but not operationalized downstream
- Amendments change terms, but billing systems continue using old assumptions
- Renewal notice windows are missed even when revenue uplift was contractually allowed
- Revenue operations teams do not have one trusted source of commercial truth

### Simple example

- Contract says 5% annual uplift with 30 days notice
- Billing stays flat
- The company loses revenue it was already entitled to charge

### Visual suggestion

- Simple left-to-right drift graphic: Quote -> Contract -> Amendment -> Billing -> Renewal
- Red drift markers between contract and billing

---

## Slide 3: The Product Story

### Slide title

This is a platform, not just one detector

### On-slide points

- Shared ingestion pipeline for contract and operational documents
- Shared clause extraction and normalization layer
- Shared governing-term resolution across conflicting documents
- Shared evidence and explanation layer for downstream agents

### Platform message

- Revenue Leakage Investigator is the first operational agent running on this platform
- The underlying evidence layer can support more agents without rebuilding the core stack

### Visual suggestion

- Platform block diagram with a shared evidence layer in the middle
- Agents shown on top: Revenue Leakage Investigator, Amendment Impact Detector, Quote-to-Contract Drift, Billing vs Contract Mismatch

---

## Slide 4: First Live Agent

### Slide title

Revenue Leakage Investigator

### On-slide points

- Detects missed uplift and renewal revenue already allowed by contract
- Predicts upcoming leakage risk before the miss happens
- Explains which document is controlling and why
- Quantifies financial impact and next action

### Current live capabilities

- Multi-document clause extraction from PDF and DOCX
- AI-assisted governing-term resolution across conflicting files
- Deterministic revenue math and risk scoring
- Source-of-record verdict with evidence traceability

### Visual suggestion

- Screenshot of the current dashboard and detail panel

---

## Slide 5: Why AI Matters

### Slide title

Why this needs AI plus deterministic logic

### On-slide points

- Rules alone are brittle for reading messy commercial language
- AI resolves clause meaning across versions and amendments
- Deterministic logic handles math, deadlines, and financial impact
- The combination is explainable, reproducible, and demo-safe

### What AI does

- Extract renewal, uplift, notice, and override language
- Resolve which document currently controls the term
- Generate case explanations and investigation briefs

### What deterministic logic does

- Revenue impact calculation
- Deadline and notice evaluation
- Queue prioritization and dashboard metrics

---

## Slide 6: How The System Decides Precedence

### Slide title

Conflicting documents are resolved, not just listed

### On-slide points

- AI first pass across the dossier
- Deterministic fallback if AI does not return a winner
- Explicit override language beats weaker references
- Amendment beats renewal notice beats order form beats MSA
- Higher version and stronger evidence win ties

### Demo examples

- Summit amendment v4 overrides earlier 4%, 6%, and 8% terms and becomes the source of record
- Redwood unrelated document is attached but does not change the governing economics

### Visual suggestion

- Small simplified decision tree or screenshot from the evidence panel

---

## Slide 7: Live Demo Flow

### Slide title

What we will show live

### Demo steps

1. Open the platform and identify Revenue Leakage Investigator as the active agent.
2. Show the dashboard summary and the two agent queues.
3. Open Summit Distribution Group and show the controlling 10% amendment, leaked revenue, and evidence chain.
4. Show the source-of-record verdict and why the latest amendment wins.
5. Switch to Redwood BioLabs and show an upcoming preventive opportunity.
6. Show that an unrelated upload is attached but does not change revenue signals.
7. Explain that the same evidence layer could support more agents next.

### Current seeded proof points

- Missed revenue detected: $65,400
- Revenue at risk: $8,250
- Summit leakage case: $38,400
- Redwood preventive opportunity: $6,000 at risk

---

## Slide 8: Why This Fits Conga

### Slide title

Why this is a strong Conga story

### On-slide points

- Strong fit with Revenue Lifecycle Management
- Uses contracts as commercial source of truth, not just legal artifacts
- Expands beyond search, Q&A, and redlining into execution intelligence
- Demonstrates a platform path, not just a one-off point solution

### Competitive angle

- Not just document retrieval
- Not just clause review
- It finds missed business action and quantifies money at stake

---

## Slide 9: Roadmap

### Slide title

What comes next on the same platform

### On-slide points

- Amendment Impact Detector
- Quote-to-Contract Drift Detector
- Billing vs Contract Mismatch Finder
- Contract Obligation Auto-Tracker

### Platform message

- Same ingestion
- Same governing-term resolution
- Same evidence layer
- Same explanation framework

---

## Slide 10: Close

### Slide title

Close

### On-slide statement

Commercial Execution Intelligence Platform turns contract truth into operational action.

### Closing line

Revenue Leakage Investigator is the first live agent, showing how AI can reconstruct the commercial source of truth, detect missed execution, and quantify the financial impact before more revenue slips away.

### Final ask

- Start with the Revenue Leakage Investigator agent
- Extend the same platform into more post-signature commercial agents