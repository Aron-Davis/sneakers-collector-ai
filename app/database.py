import sqlite3
from pathlib import Path
from typing import Any

from .models import SneakerCreate


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "collection.db"

UPDATABLE_FIELDS = {
    "colorway",
    "style_code",
    "size",
    "size_system",
    "condition",
    "purchase_price",
    "currency",
    "purchase_date",
    "has_box",
    "notes",
}


def get_connection() -> sqlite3.Connection:
    """Apre una connessione SQLite configurata per restituire righe indicizzabili per nome."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_database() -> None:
    """Crea la tabella delle sneakers se non esiste già."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sneakers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                colorway TEXT,
                style_code TEXT,
                size REAL,
                size_system TEXT DEFAULT 'EU',
                condition TEXT,
                purchase_price REAL,
                currency TEXT DEFAULT 'EUR',
                purchase_date TEXT,
                has_box INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def add_sneaker(sneaker: SneakerCreate) -> int:
    """Inserisce una sneaker nella collezione e restituisce il relativo ID."""
    data = sneaker.model_dump(mode="json")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO sneakers (
                brand,
                model,
                colorway,
                style_code,
                size,
                size_system,
                condition,
                purchase_price,
                currency,
                purchase_date,
                has_box,
                notes
            )
            VALUES (
                :brand,
                :model,
                :colorway,
                :style_code,
                :size,
                :size_system,
                :condition,
                :purchase_price,
                :currency,
                :purchase_date,
                :has_box,
                :notes
            )
            """,
            data,
        )
        return cursor.lastrowid


def update_sneaker(sneaker_id: int, updates: dict[str, Any]) -> bool:
    """Aggiorna i campi consentiti di una sneaker identificata dal suo ID."""
    safe_updates = {
        key: value
        for key, value in updates.items()
        if key in UPDATABLE_FIELDS
    }

    if not safe_updates:
        return False

    assignments = ", ".join(
        f"{field} = :{field}"
        for field in safe_updates
    )
    parameters = {
        **safe_updates,
        "sneaker_id": sneaker_id,
    }

    with get_connection() as connection:
        cursor = connection.execute(f" UPDATE sneakers SET {assignments} WHERE id = :sneaker_id", parameters)
        return cursor.rowcount > 0


def delete_sneaker(sneaker_id: int) -> bool:
    """Elimina una sneaker tramite ID e indica se è stata rimossa una riga."""
    with get_connection() as connection:
        cursor = connection.execute(" DELETE FROM sneakers WHERE id = ?", (sneaker_id,))
        return cursor.rowcount > 0


def get_all_sneakers() -> list[dict[str, Any]]:
    """Restituisce tutte le sneakers ordinate dalla più recente."""
    with get_connection() as connection:
        rows = connection.execute(" SELECT * FROM sneakers ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


def get_sneaker_by_id(sneaker_id: int) -> dict[str, Any] | None:
    """Restituisce una sneaker tramite ID oppure None se non esiste."""
    with get_connection() as connection:
        row = connection.execute(" SELECT * FROM sneakers WHERE id = ?", (sneaker_id,)).fetchone()

        if row is None:
            return None

        return dict(row)


def search_sneakers(query: str) -> list[dict[str, Any]]:
    """Cerca sneakers richiedendo la corrispondenza di tutti i termini della query."""
    terms = [
        term.strip().lower()
        for term in query.split()
        if term.strip()
    ]

    if not terms:
        return []

    searchable_text = """
        LOWER(
            COALESCE(brand, '') || ' ' ||
            COALESCE(model, '') || ' ' ||
            COALESCE(colorway, '') || ' ' ||
            COALESCE(style_code, '')
        )
    """
    where_clause = " AND ".join(f"{searchable_text} LIKE ?" for _ in terms)
    parameters = [f"%{term}%" for term in terms]

    with get_connection() as connection:
        rows = connection.execute(f" SELECT * FROM sneakers WHERE {where_clause} ORDER BY id", parameters).fetchall()
        return [dict(row) for row in rows]


def get_collection_stats() -> dict[str, Any]:
    """Calcola numero di paia, brand distinti e statistiche di spesa per valuta."""
    with get_connection() as connection:
        general = connection.execute(" SELECT COUNT(*) AS total_pairs, COUNT(DISTINCT brand) AS total_brands FROM sneakers").fetchone()

        spending_rows = connection.execute(
            """
            SELECT
                currency,
                SUM(purchase_price) AS total_spent,
                AVG(purchase_price) AS average_price
            FROM sneakers
            WHERE purchase_price IS NOT NULL
            GROUP BY currency
            """
        ).fetchall()

        return {
            "total_pairs": general["total_pairs"],
            "total_brands": general["total_brands"],
            "spending_by_currency": [dict(row) for row in spending_rows]
        }
