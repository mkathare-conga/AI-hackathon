"""
Setup service — CRUD for accounts, contracts, and invoice lines.
Used by the demo setup UI to create and manage test data without touching the DB directly.
"""
from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path


def _conn():
    import psycopg
    from psycopg.rows import dict_row

    from app.config import get_data_settings

    settings = get_data_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured")
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


def _bust_cache() -> None:
    """Clear lru_cache on all data-loader functions so new rows are immediately visible."""
    from app.data_loader import (
        load_accounts, load_contracts, load_invoice_lines, load_renewal_events,
    )
    load_accounts.cache_clear()
    load_contracts.cache_clear()
    load_invoice_lines.cache_clear()
    load_renewal_events.cache_clear()


# ─── Reset ────────────────────────────────────────────────────────────────────

def reset_to_seed() -> dict:
    """Truncate all tables and re-run the seed SQL, then clear MinIO."""
    seed_path = Path(__file__).resolve().parent.parent.parent / "docker" / "postgres" / "init" / "002_seed.sql"
    if not seed_path.exists():
        raise RuntimeError(f"Seed SQL not found at {seed_path}")
    seed_sql = seed_path.read_text(encoding="utf-8")

    with _conn() as conn:
        with conn.cursor() as cur:
            # Truncate leaf→root order to satisfy FK constraints cleanly
            cur.execute("""
                TRUNCATE TABLE
                    obligation_extractions,
                    renewal_events,
                    invoice_lines,
                    contract_documents,
                    contracts,
                    accounts
                CASCADE
            """)
            conn.commit()
        with conn.cursor() as cur:
            cur.execute(seed_sql)
            conn.commit()

    _bust_cache()

    # Clear MinIO bucket (best-effort — ignore if not configured)
    try:
        from app.object_store import get_minio_client
        from app.config import get_object_store_settings
        settings = get_object_store_settings()
        if settings.configured:
            client = get_minio_client()
            bucket = settings.bucket
            objects = client.list_objects(bucket, recursive=True)
            for obj in objects:
                client.remove_object(bucket, obj.object_name)
    except Exception:
        pass  # MinIO is optional; don't fail the reset if it's unavailable

    return {"status": "ok", "message": "Reset to seed data complete"}


# ─── Accounts ─────────────────────────────────────────────────────────────────

def list_accounts_with_stats() -> list[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    a.account_id,
                    a.name,
                    COUNT(DISTINCT c.contract_id) AS contract_count,
                    COUNT(DISTINCT il.invoice_id) AS invoice_count,
                    MIN(c.contract_id) AS primary_contract_id
                FROM accounts a
                LEFT JOIN contracts c ON c.account_id = a.account_id
                LEFT JOIN invoice_lines il ON il.account_id = a.account_id
                GROUP BY a.account_id, a.name
                ORDER BY a.name
            """)
            return cur.fetchall()


def create_account(name: str) -> dict:
    account_id = f"acc-{_short_id()}"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO accounts (account_id, name) VALUES (%s, %s) RETURNING account_id, name",
                (account_id, name),
            )
            conn.commit()
            result = cur.fetchone()
    _bust_cache()
    return result


def delete_account(account_id: str) -> bool:
    """Cascade-deletes contracts → invoice_lines → obligation_extractions, etc."""
    with _conn() as conn:
        with conn.cursor() as cur:
            # Delete invoice lines first (FK to account)
            cur.execute("DELETE FROM invoice_lines WHERE account_id = %s", (account_id,))
            # Delete contracts (cascade will remove documents, obligations, renewal_events)
            cur.execute("DELETE FROM contracts WHERE account_id = %s", (account_id,))
            cur.execute("DELETE FROM accounts WHERE account_id = %s", (account_id,))
            conn.commit()
            deleted = cur.rowcount > 0
    _bust_cache()
    return deleted


# ─── Contracts ────────────────────────────────────────────────────────────────

def list_contracts_for_account(account_id: str) -> list[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.contract_id,
                    c.product_name,
                    c.term_start,
                    c.term_end,
                    c.base_price,
                    c.currency,
                    c.quantity,
                    COUNT(il.invoice_id) AS invoice_count,
                    CASE
                        WHEN g.effective_date IS NOT NULL THEN
                            (g.effective_date - g.notice_window_days - CURRENT_DATE)
                        ELSE NULL
                    END AS days_until_deadline
                FROM contracts c
                LEFT JOIN invoice_lines il ON il.contract_id = c.contract_id
                LEFT JOIN LATERAL (
                    SELECT effective_date, notice_window_days
                    FROM obligation_extractions
                    WHERE contract_id = c.contract_id
                    ORDER BY confidence_score DESC
                    LIMIT 1
                ) g ON true
                WHERE c.account_id = %s
                GROUP BY c.contract_id, c.product_name, c.term_start, c.term_end,
                         c.base_price, c.currency, c.quantity,
                         g.effective_date, g.notice_window_days
                ORDER BY c.term_start
            """, (account_id,))
            return cur.fetchall()


def create_contract(
    account_id: str,
    product_name: str,
    term_start: date,
    term_end: date,
    base_price: float,
    currency: str,
    quantity: int,
    uplift_pct: float,
) -> dict:
    contract_id = f"ctr-{_short_id()}"
    raw_text = (
        f"SUBSCRIPTION AGREEMENT\n\n"
        f"Product: {product_name}\n"
        f"Term: {term_start} to {term_end}\n"
        f"Base Price: {currency} {base_price:,.2f} per unit × {quantity} units\n\n"
        f"Section 7.2 — Annual Uplift\n"
        f"The subscription fee shall increase by {uplift_pct:.1f}% on each anniversary of the Term Start Date, "
        f"provided that Seller delivers written notice no fewer than 30 days prior to such anniversary."
    )
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO contracts
                    (contract_id, account_id, product_name, term_start, term_end,
                     base_price, currency, quantity, raw_contract_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING contract_id, product_name, term_start, term_end,
                          base_price, currency, quantity
                """,
                (contract_id, account_id, product_name, term_start, term_end,
                 base_price, currency, quantity, raw_text),
            )
            conn.commit()
            result = cur.fetchone()
    _bust_cache()
    return result


def delete_contract(contract_id: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM invoice_lines WHERE contract_id = %s", (contract_id,))
            cur.execute("DELETE FROM contracts WHERE contract_id = %s", (contract_id,))
            conn.commit()
            deleted = cur.rowcount > 0
    _bust_cache()
    return deleted


def shift_renewal(contract_id: str, days_from_today: int) -> dict:
    """
    Set the notice deadline to be `days_from_today` days from today.
    Updates all obligation_extractions.effective_date and contracts.term_end.

    days_until_deadline = (effective_date - notice_window_days - today).days
    So: effective_date = today + days_from_today + notice_window_days
    """
    from datetime import datetime
    today = datetime.utcnow().date()

    with _conn() as conn:
        with conn.cursor() as cur:
            # Get the governing obligation's notice_window_days and current effective_date
            cur.execute("""
                SELECT effective_date, notice_window_days
                FROM obligation_extractions
                WHERE contract_id = %s
                ORDER BY confidence_score DESC
                LIMIT 1
            """, (contract_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"No obligation extractions found for contract {contract_id}")

            notice_window_days = row["notice_window_days"]
            current_effective_date = row["effective_date"]

            # Compute new effective_date from desired days_until_deadline
            from datetime import timedelta
            new_effective_date = today + timedelta(days=days_from_today + notice_window_days)
            offset_days = (new_effective_date - current_effective_date).days

            # Shift all obligations for this contract by the same offset
            cur.execute("""
                UPDATE obligation_extractions
                SET effective_date = effective_date + (%s * INTERVAL '1 day')
                WHERE contract_id = %s
            """, (offset_days, contract_id))

            # Update term_end to the day before the new effective_date
            new_term_end = new_effective_date - timedelta(days=1)
            cur.execute("""
                UPDATE contracts SET term_end = %s WHERE contract_id = %s
            """, (new_term_end, contract_id))

            conn.commit()

    _bust_cache()
    return {
        "contract_id": contract_id,
        "new_effective_date": new_effective_date.isoformat(),
        "days_until_deadline": days_from_today,
    }


# ─── Invoice Lines ────────────────────────────────────────────────────────────

def list_invoice_lines_for_contract(contract_id: str) -> list[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT invoice_id, billing_period_start, billing_period_end,
                       amount_billed, quantity
                FROM invoice_lines
                WHERE contract_id = %s
                ORDER BY billing_period_start
            """, (contract_id,))
            return cur.fetchall()


def create_invoice_line(
    account_id: str,
    contract_id: str,
    billing_period_start: date,
    billing_period_end: date,
    amount_billed: float,
    quantity: int,
) -> dict:
    invoice_id = f"inv-{_short_id()}"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO invoice_lines
                    (invoice_id, account_id, contract_id,
                     billing_period_start, billing_period_end, amount_billed, quantity)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING invoice_id, billing_period_start, billing_period_end,
                          amount_billed, quantity
                """,
                (invoice_id, account_id, contract_id,
                 billing_period_start, billing_period_end, amount_billed, quantity),
            )
            conn.commit()
            result = cur.fetchone()
    _bust_cache()
    return result


def delete_invoice_line(invoice_id: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM invoice_lines WHERE invoice_id = %s", (invoice_id,))
            conn.commit()
            deleted = cur.rowcount > 0
    _bust_cache()
    return deleted
