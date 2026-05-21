from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_data_settings
from app.models import Account, Contract, ContractDocument, InvoiceLine, PersistedObligationExtraction, RenewalEvent
from app.postgres_loader import (
    load_accounts_from_postgres,
    load_contract_documents_from_postgres,
    load_contracts_from_postgres,
    load_invoice_lines_from_postgres,
    load_obligation_extractions_from_postgres,
    load_renewal_events_from_postgres,
)


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "revenue_leakage"


def _load_json_file(name: str) -> Any:
    file_path = DATA_DIR / name
    with file_path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


@lru_cache(maxsize=1)
def load_accounts() -> list[Account]:
    if get_data_settings().use_postgres:
        return load_accounts_from_postgres()
    return [Account.model_validate(item) for item in _load_json_file("accounts.json")]


@lru_cache(maxsize=1)
def load_contracts() -> list[Contract]:
    if get_data_settings().use_postgres:
        return load_contracts_from_postgres()
    return [Contract.model_validate(item) for item in _load_json_file("contracts.json")]


@lru_cache(maxsize=1)
def load_invoice_lines() -> list[InvoiceLine]:
    if get_data_settings().use_postgres:
        return load_invoice_lines_from_postgres()
    return [InvoiceLine.model_validate(item) for item in _load_json_file("invoice_lines.json")]


@lru_cache(maxsize=1)
def load_renewal_events() -> list[RenewalEvent]:
    if get_data_settings().use_postgres:
        return load_renewal_events_from_postgres()
    return [RenewalEvent.model_validate(item) for item in _load_json_file("renewal_events.json")]


def load_contract_documents(contract_id: str | None = None) -> list[ContractDocument]:
    if get_data_settings().use_postgres:
        return load_contract_documents_from_postgres(contract_id=contract_id)
    return []


def load_obligation_extractions(contract_id: str | None = None) -> list[PersistedObligationExtraction]:
    if get_data_settings().use_postgres:
        return load_obligation_extractions_from_postgres(contract_id=contract_id)
    return []
