from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.models import AIInvestigationBrief, DocumentImportResponse
from app.services.ai_integration import get_ai_status
from app.services.document_ingestion import import_contract_document
from app.services.documents import get_contract_document_bytes
from app.services.leakage import (
    get_contract_ai_brief,
    get_contract_facts,
    get_dashboard_summary,
    get_leakage_case,
    get_leakage_cases,
    get_risk_prediction,
    get_risk_predictions,
)
from app.services import setup as setup_svc
from app.services import drift as drift_svc
from app.services import amendment_impact as amendment_svc


app = FastAPI(
    title="Revenue Leakage Investigator",
    version="0.1.0",
    summary="Hackathon MVP for missed renewal and uplift detection.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Revenue Leakage Investigator",
        "agent": "Missed Renewal/Uplift Finder",
        "status": "ready-for-demo",
    }


@app.get("/api/system/ai-status")
def ai_status():
    return get_ai_status()


@app.get("/api/accounts")
def list_accounts():
    """All accounts with their primary contract_id — used by the Investigate sidebar."""
    return setup_svc.list_accounts_with_stats()


@app.get("/api/dashboard/summary")
def dashboard_summary():
    return get_dashboard_summary()


@app.get("/api/cases")
def list_cases():
    return get_leakage_cases()


@app.get("/api/cases/{case_id}")
def case_detail(case_id: str):
    case = get_leakage_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.get("/api/predictions")
def list_predictions():
    return get_risk_predictions()


@app.get("/api/predictions/{prediction_id}")
def prediction_detail(prediction_id: str):
    prediction = get_risk_prediction(prediction_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@app.get("/api/contracts/{contract_id}/facts")
def contract_facts(contract_id: str):
    facts = get_contract_facts(contract_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return facts


@app.get("/api/contracts/{contract_id}/ai-brief", response_model=AIInvestigationBrief)
def contract_ai_brief(
    contract_id: str,
    focus: Literal["contract", "case", "prediction"] = "contract",
):
    brief = get_contract_ai_brief(contract_id, focus=focus)
    if brief is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return brief


@app.get("/api/documents/{document_id}/content")
def document_content(document_id: str):
    result = get_contract_document_bytes(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")

    document, payload = result
    disposition_type = "inline" if document.mime_type == "application/pdf" else "attachment"
    return Response(
        content=payload,
        media_type=document.mime_type,
        headers={"Content-Disposition": f'{disposition_type}; filename="{document.file_name}"'},
    )


@app.post("/api/contracts/{contract_id}/documents/import", response_model=DocumentImportResponse)
async def import_document(
    contract_id: str,
    document_type: Annotated[
        Literal["msa", "nda", "order_form", "amendment", "renewal_notice"],
        Form(),
    ],
    file: Annotated[UploadFile, File()],
):
    try:
        payload = await file.read()
        return import_contract_document(
            contract_id=contract_id,
            document_type=document_type,
            file_name=file.filename or "uploaded-document",
            content_type=file.content_type,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─── Setup / Demo Data API ────────────────────────────────────────────────────

@app.get("/api/setup/accounts")
def setup_list_accounts():
    return setup_svc.list_accounts_with_stats()


@app.post("/api/setup/accounts", status_code=201)
def setup_create_account(body: dict):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    return setup_svc.create_account(name)


@app.delete("/api/setup/accounts/{account_id}", status_code=204)
def setup_delete_account(account_id: str):
    setup_svc.delete_account(account_id)


@app.get("/api/setup/accounts/{account_id}/contracts")
def setup_list_contracts(account_id: str):
    return setup_svc.list_contracts_for_account(account_id)


@app.post("/api/setup/accounts/{account_id}/contracts", status_code=201)
def setup_create_contract(account_id: str, body: dict):
    from datetime import date
    required = ["product_name", "term_start", "term_end", "base_price", "quantity"]
    for field in required:
        if not body.get(field):
            raise HTTPException(status_code=400, detail=f"{field} is required")
    try:
        return setup_svc.create_contract(
            account_id=account_id,
            product_name=body["product_name"],
            term_start=date.fromisoformat(body["term_start"]),
            term_end=date.fromisoformat(body["term_end"]),
            base_price=float(body["base_price"]),
            currency=body.get("currency", "USD"),
            quantity=int(body["quantity"]),
            uplift_pct=float(body.get("uplift_pct", 0)),
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/setup/contracts/{contract_id}", status_code=204)
def setup_delete_contract(contract_id: str):
    setup_svc.delete_contract(contract_id)


@app.post("/api/setup/contracts/{contract_id}/shift-renewal")
def setup_shift_renewal(contract_id: str, body: dict):
    days = body.get("days_from_today")
    if days is None or not isinstance(days, int) or days < 0:
        raise HTTPException(status_code=400, detail="days_from_today must be a non-negative integer")
    try:
        return setup_svc.shift_renewal(contract_id, days)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/setup/contracts/{contract_id}/invoices")
def setup_list_invoices(contract_id: str):
    return setup_svc.list_invoice_lines_for_contract(contract_id)


@app.post("/api/setup/contracts/{contract_id}/invoices", status_code=201)
def setup_create_invoice(contract_id: str, body: dict):
    from datetime import date
    required = ["account_id", "billing_period_start", "billing_period_end", "amount_billed", "quantity"]
    for field in required:
        if body.get(field) is None:
            raise HTTPException(status_code=400, detail=f"{field} is required")
    try:
        return setup_svc.create_invoice_line(
            account_id=body["account_id"],
            contract_id=contract_id,
            billing_period_start=date.fromisoformat(body["billing_period_start"]),
            billing_period_end=date.fromisoformat(body["billing_period_end"]),
            amount_billed=float(body["amount_billed"]),
            quantity=int(body["quantity"]),
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/setup/invoices/{invoice_id}", status_code=204)
def setup_delete_invoice(invoice_id: str):
    setup_svc.delete_invoice_line(invoice_id)


@app.post("/api/setup/reset")
def setup_reset():
    try:
        return setup_svc.reset_to_seed()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─── Quote-to-Contract Drift Detector API ─────────────────────────────────────

@app.get("/api/drift/dashboard")
def drift_dashboard():
    return drift_svc.get_drift_dashboard()


@app.get("/api/drift/quotes")
def drift_list_quotes():
    return drift_svc.list_quotes()


@app.get("/api/drift/quotes/{quote_id}")
def drift_get_quote(quote_id: str):
    quote = drift_svc.get_quote(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@app.get("/api/drift/quotes/{quote_id}/lines")
def drift_get_quote_lines(quote_id: str):
    return drift_svc.get_quote_lines(quote_id)


@app.get("/api/drift/contracts")
def drift_list_contracts():
    return drift_svc.list_drift_contracts()


@app.get("/api/drift/contracts/{contract_id}")
def drift_get_contract(contract_id: str):
    contract = drift_svc.get_drift_contract(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@app.get("/api/drift/findings")
def drift_list_findings(quote_id: str | None = None):
    return drift_svc.list_findings(quote_id)


@app.get("/api/drift/findings/{finding_id}")
def drift_get_finding(finding_id: str):
    finding = drift_svc.get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@app.post("/api/drift/analyze")
def drift_analyze(body: dict):
    quote_id = body.get("quote_id")
    contract_id = body.get("contract_id")
    if not quote_id or not contract_id:
        raise HTTPException(status_code=400, detail="quote_id and contract_id are required")
    try:
        return drift_svc.run_drift_analysis(quote_id, contract_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/drift/analyze-all")
def drift_analyze_all():
    return drift_svc.analyze_all_quotes()


# ─── Amendment Impact Detector API ────────────────────────────────────────────

@app.get("/api/amendments/dashboard")
def amendment_dashboard():
    return amendment_svc.get_amendment_dashboard()


@app.get("/api/amendments/analyses")
def amendment_list_analyses():
    return amendment_svc.list_analyses()


@app.get("/api/amendments/analyses/{analysis_id}")
def amendment_get_analysis(analysis_id: str):
    detail = amendment_svc.get_analysis_detail(analysis_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return detail


@app.get("/api/amendments/analyses/{analysis_id}/impacts")
def amendment_list_impacts(analysis_id: str):
    return amendment_svc.list_impacts(analysis_id)


@app.get("/api/amendments/analyses/{analysis_id}/actions")
def amendment_list_actions(analysis_id: str, status: str | None = None):
    return amendment_svc.list_action_items(analysis_id=analysis_id, status=status)


@app.patch("/api/amendments/actions/{action_id}")
def amendment_update_action(action_id: str, body: dict):
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status is required")
    try:
        result = amendment_svc.update_action_status(action_id, new_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Action item not found")
    return result


@app.post("/api/amendments/analyze")
async def amendment_analyze(
    contract_id: Annotated[str, Form()],
    account_name: Annotated[str, Form()],
    amendment_date: Annotated[str, Form()],
    original_contract: Annotated[UploadFile, File()],
    amendment: Annotated[UploadFile, File()],
):
    """Upload an original contract and amendment to analyze impacts."""
    try:
        original_text = (await original_contract.read()).decode("utf-8", errors="replace")
        amendment_text = (await amendment.read()).decode("utf-8", errors="replace")
        return amendment_svc.analyze_amendment_text(
            contract_id=contract_id,
            account_name=account_name,
            original_contract_text=original_text,
            amendment_text=amendment_text,
            amendment_date=amendment_date,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

