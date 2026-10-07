from .database import (
    delete_sneaker as db_delete_sneaker,
    get_all_sneakers,
    get_collection_stats,
    get_sneaker_by_id,
    search_sneakers,
    update_sneaker as db_update_sneaker,
)
from .models import SneakerResponse


def serialize_sneaker(data: dict | None) -> dict | None:
    """Serializza i dati di una sneaker secondo lo schema di risposta."""
    if data is None:
        return None

    return SneakerResponse.model_validate(data).model_dump(mode="json")


def list_collection() -> list[dict]:
    """Restituisce tutte le sneaker presenti nella collezione."""
    sneakers = get_all_sneakers()

    return [serialize_sneaker(sneaker) for sneaker in sneakers]


def search_collection(query: str) -> list[dict]:
    """Cerca sneaker nella collezione usando una query testuale."""
    sneakers = search_sneakers(query)

    return [serialize_sneaker(sneaker) for sneaker in sneakers]


def sneaker_by_id(sneaker_id: int) -> dict | None:
    """Restituisce una sneaker tramite il relativo ID di database."""
    sneaker = get_sneaker_by_id(sneaker_id)

    return serialize_sneaker(sneaker)


def collection_stats() -> dict:
    """Restituisce le statistiche aggregate della collezione."""
    return get_collection_stats()


def update_sneaker_fields(sneaker_id: int, updates: dict) -> dict | None:
    """Aggiorna i campi consentiti di una sneaker e restituisce il record aggiornato."""
    updated = db_update_sneaker(sneaker_id, updates)

    if not updated:
        return None

    return sneaker_by_id(sneaker_id)


def remove_sneaker(sneaker_id: int) -> bool:
    """Elimina una sneaker tramite ID e indica se la cancellazione è avvenuta."""
    return db_delete_sneaker(sneaker_id)
