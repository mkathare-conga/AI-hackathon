from __future__ import annotations

from app.config import get_object_store_settings
from app.data_loader import load_contract_documents
from app.models import ContractDocument
from app.object_store import get_minio_client


def list_contract_documents(contract_id: str) -> list[ContractDocument]:
    return load_contract_documents(contract_id=contract_id)


def get_contract_document(document_id: str) -> ContractDocument | None:
    for document in load_contract_documents():
        if document.document_id == document_id:
            return document
    return None


def get_contract_document_bytes(document_id: str) -> tuple[ContractDocument, bytes] | None:
    document = get_contract_document(document_id)
    if document is None:
        return None

    client = get_minio_client()
    response = client.get_object(get_object_store_settings().bucket_name, document.storage_key)
    try:
        payload = response.read()
    finally:
        response.close()
        response.release_conn()

    return document, payload