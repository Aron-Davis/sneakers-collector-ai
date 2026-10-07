import pytest

from app.agent import format_amount, format_tool_response


# Verifica la formattazione delle statistiche aggregate della collezione.
def test_format_collection_stats():
    result = {
        "total_pairs": 4,
        "total_brands": 2,
        "spending_by_currency": [
            {
                "currency": "EUR",
                "total_spent": 530,
                "average_price": 132.5,
            }
        ],
    }

    response = format_tool_response("collection_stats", result)

    assert "4 sneakers" in response
    assert "2 brand" in response
    assert "530 EUR" in response
    assert "132.5 EUR" in response


# Verifica il messaggio restituito quando una ricerca non produce risultati.
def test_format_empty_search():
    response = format_tool_response("search_collection", [])

    assert response == "Non ho trovato sneakers corrispondenti alla ricerca."


# Verifica la formattazione di più risultati restituiti dalla ricerca.
def test_format_search_results():
    result = [
        {
            "brand": "Nike",
            "model": "Air Jordan 1",
            "colorway": "Chicago",
        },
        {
            "brand": "Adidas",
            "model": "Samba OG",
            "colorway": "White Black",
        },
    ]

    response = format_tool_response("search_collection", result)

    assert "2 sneakers" in response
    assert "Nike Air Jordan 1 Chicago" in response
    assert "Adidas Samba OG White Black" in response


# Verifica il messaggio restituito quando la ricerca per ID non trova una sneaker.
def test_format_sneaker_by_id_not_found():
    response = format_tool_response("sneaker_by_id", None)

    assert response == "Non ho trovato una sneaker con questo ID."


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (530, "530"),
        (530.0, "530"),
        (132.5, "132.5"),
        (132.55, "132.55"),
    ],
)
# Verifica che gli importi mantengano solo le cifre decimali significative.
def test_format_amount(value, expected):
    assert format_amount(value) == expected
