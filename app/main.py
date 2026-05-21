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

