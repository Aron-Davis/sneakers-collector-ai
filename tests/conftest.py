from pathlib import Path

import pytest

import app.database as database


@pytest.fixture
def temp_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Crea un database SQLite temporaneo e isolato per ciascun test."""
    test_db_path = tmp_path / "test_collection.db"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    database.create_database()

    return test_db_path
