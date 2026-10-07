import pytest

import app.database as database
from app.models import SneakerCreate


# Verifica inserimento e recupero di una sneaker tramite ID.
def test_add_and_get_sneaker(temp_database):
    sneaker = SneakerCreate(
        brand="Nike",
        model="Air Max 1",
        colorway="Anniversary Red",
        size=43,
        size_system="EU",
        condition="used",
        purchase_price=150,
        currency="EUR",
        has_box=True,
    )

    sneaker_id = database.add_sneaker(sneaker)
    result = database.get_sneaker_by_id(sneaker_id)

    assert result is not None
    assert result["id"] == sneaker_id
    assert result["brand"] == "Nike"
    assert result["model"] == "Air Max 1"
    assert result["colorway"] == "Anniversary Red"
    assert result["size"] == 43
    assert result["purchase_price"] == 150


# Verifica il recupero dell'intera collezione dal database.
def test_get_all_sneakers(temp_database):
    database.add_sneaker(SneakerCreate(brand="Nike", model="Air Jordan 1"))
    database.add_sneaker(SneakerCreate(brand="Adidas", model="Samba OG"))

    sneakers = database.get_all_sneakers()
    brands = [sneaker["brand"] for sneaker in sneakers]

    assert len(sneakers) == 2
    assert "Nike" in brands
    assert "Adidas" in brands


# Verifica la ricerca delle sneakers tramite testo libero.
def test_search_sneakers(temp_database):
    database.add_sneaker(SneakerCreate(brand="Nike", model="Air Jordan 1", colorway="Chicago"))
    database.add_sneaker(SneakerCreate(brand="Adidas", model="Samba OG", colorway="White Black"))

    results = database.search_sneakers("Nike")

    assert len(results) == 1
    assert results[0]["brand"] == "Nike"
    assert results[0]["model"] == "Air Jordan 1"


# Verifica l'eliminazione di una sneaker tramite ID.
def test_delete_sneaker(temp_database):
    sneaker_id = database.add_sneaker(SneakerCreate(brand="Asics", model="Gel-Kayano 14"))

    assert database.get_sneaker_by_id(sneaker_id) is not None

    database.delete_sneaker(sneaker_id)

    assert database.get_sneaker_by_id(sneaker_id) is None


# Verifica il calcolo delle statistiche aggregate della collezione.
def test_collection_stats(temp_database):
    database.add_sneaker(SneakerCreate(brand="Nike", model="Air Max 1", purchase_price=100, currency="EUR"))
    database.add_sneaker(SneakerCreate(brand="Adidas", model="Samba OG", purchase_price=200, currency="EUR"))
    database.add_sneaker(SneakerCreate(brand="New Balance", model="990v6", purchase_price=180, currency="USD"))

    stats = database.get_collection_stats()
    spending = {
        item["currency"]: item
        for item in stats["spending_by_currency"]
    }

    assert stats["total_pairs"] == 3
    assert stats["total_brands"] == 3
    assert spending["EUR"]["total_spent"] == 300
    assert spending["EUR"]["average_price"] == pytest.approx(150)
    assert spending["USD"]["total_spent"] == 180
    assert spending["USD"]["average_price"] == pytest.approx(180)
