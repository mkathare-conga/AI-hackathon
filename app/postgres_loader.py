from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from app.config import get_data_settings
from app.models import Account, Contract, ContractDocument, InvoiceLine, PersistedObligationExtraction, RenewalEvent


ModelT = TypeVar("ModelT", bound=BaseModel)


def _load_records(query: str, model_type: type[ModelT], params: tuple[Any, ...] = ()) -> list[ModelT]:
    import psycopg
    from psycopg.rows import dict_row

    settings = get_data_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured when DATA_SOURCE=postgres")

    with psycopg.connect(settings.database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return [model_type.model_validate(row) for row in cursor.fetchall()]


def load_accounts_from_postgres() -> list[Account]:
    return _load_records(
        "SELECT account_id, name FROM accounts ORDER BY account_id",
        Account,
    )


def load_contracts_from_postgres() -> list[Contract]:
    return _load_records(
        (
            "SELECT contract_id, account_id, product_name, term_start, term_end, base_price, currency, quantity, raw_contract_text "
            "FROM contracts ORDER BY contract_id"
        ),
        Contract,
    )


def load_invoice_lines_from_postgres() -> list[InvoiceLine]:
    return _load_records(
        (
            "SELECT invoice_id, account_id, contract_id, billing_period_start, billing_period_end, amount_billed, quantity "
            "FROM invoice_lines ORDER BY billing_period_start, invoice_id"
        ),
        InvoiceLine,
    )


def load_renewal_events_from_postgres() -> list[RenewalEvent]:
    return _load_records(
        "SELECT contract_id, event_type, event_date FROM renewal_events ORDER BY event_date, contract_id",
        RenewalEvent,
    )


def load_contract_documents_from_postgres(contract_id: str | None = None) -> list[ContractDocument]:
    base_query = (
        "SELECT document_id, contract_id, document_type, file_name, mime_type, storage_key, version, page_count, ingestion_status "
        "FROM contract_documents"
    )
    if contract_id is None:
        return _load_records(f"{base_query} ORDER BY contract_id, version, document_id", ContractDocument)
    return _load_records(
        f"{base_query} WHERE contract_id = %s ORDER BY version, document_id",
        ContractDocument,
        (contract_id,),
    )


def load_obligation_extractions_from_postgres(contract_id: str | None = None) -> list[PersistedObligationExtraction]:
    base_query = (
        "SELECT extraction_id, contract_id, document_id, obligation_type, value, effective_date, notice_window_days, "
        "source_clause_text, page_number, confidence_score, extraction_method "
        "FROM obligation_extractions WHERE effective_date IS NOT NULL AND notice_window_days IS NOT NULL"
    )
    if contract_id is None:
        return _load_records(
            f"{base_query} ORDER BY contract_id, confidence_score DESC, extraction_id",
            PersistedObligationExtraction,
        )
    return _load_records(
        f"{base_query} AND contract_id = %s ORDER BY confidence_score DESC, extraction_id",
        PersistedObligationExtraction,
        (contract_id,),
    )


def load_document_extracted_text(document_id: str) -> tuple[str, str | None, int | None] | None:
    """Load pre-extracted text from DB instead of re-fetching from MinIO."""
    import psycopg
    from psycopg.rows import dict_row

    settings = get_data_settings()
    if not settings.database_url:
        return None

    with psycopg.connect(settings.database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT extracted_text, commercial_excerpt, page_count FROM contract_documents WHERE document_id = %s",
                (document_id,),
            )
            row = cursor.fetchone()
            if row is None or row["extracted_text"] is None:
                return None
            return (row["extracted_text"], row["commercial_excerpt"], row["page_count"])
