from uuid import uuid4

import pytest

import app.database as database
import app.graph as graph
from app.models import (
    AddSneakerDecision,
    DeleteSneakerDecision,
    SneakerCreate,
    SneakerExtraction,
    SneakerKnowledgeDecision,
    SneakerUpdate,
    UpdateSneakerDecision,
)


# Crea una sneaker di test persistita nel database temporaneo.
def create_test_sneaker():
    sneaker = SneakerCreate(
        brand="Adidas",
        model="Samba OG",
        colorway="White Black",
        size=43,
        size_system="EU",
        condition="used",
        purchase_price=100,
        currency="EUR",
        has_box=True,
    )
    return database.add_sneaker(sneaker)


# Sostituisce router ed estrazione LLM per isolare il workflow di aggiunta.
@pytest.fixture
def mocked_add_flow(monkeypatch):
    def fake_decide_action(text):
        return AddSneakerDecision(action="add_sneaker")

    def fake_parse_sneaker_text(text):
        return SneakerExtraction(
            brand="Adidas",
            model="Samba OG",
            colorway="White Black",
            size=43,
            size_system="EU",
            condition="used",
            purchase_price=100,
            currency="EUR",
            has_box=True,
        )

    monkeypatch.setattr(graph, "decide_action", fake_decide_action)
    monkeypatch.setattr(graph, "parse_sneaker_text", fake_parse_sneaker_text)


# Verifica che annullare un'aggiunta non salvi alcuna sneaker.
def test_add_sneaker_cancelled(temp_database, mocked_add_flow):
    thread_id = f"test-cancel-{uuid4()}"

    preview = graph.run_graph("Aggiungi una sneaker", thread_id)

    assert preview["status"] == "awaiting_confirmation"
    assert preview["action"] == "add_sneaker"
    assert len(database.get_all_sneakers()) == 0

    result = graph.resume_graph(thread_id=thread_id, approved=False)

    assert result["status"] == "cancelled"
    assert len(database.get_all_sneakers()) == 0


# Verifica che la preview di aggiunta non persista dati prima della conferma.
def test_preview_does_not_save(temp_database, mocked_add_flow):
    thread_id = f"test-preview-{uuid4()}"

    result = graph.run_graph("Aggiungi una sneaker", thread_id)

    assert result["status"] == "awaiting_confirmation"
    assert len(database.get_all_sneakers()) == 0


# Verifica che un thread concluso non possa essere ripreso una seconda volta.
def test_completed_thread_cannot_be_resumed(temp_database, mocked_add_flow):
    thread_id = f"test-completed-{uuid4()}"

    graph.run_graph("Aggiungi una sneaker", thread_id)
    result = graph.resume_graph(thread_id=thread_id, approved=False)

    assert result["status"] == "cancelled"

    with pytest.raises(ValueError):
        graph.resume_graph(thread_id=thread_id, approved=True)


# Verifica che confermare un'aggiunta persista correttamente la sneaker.
def test_add_sneaker_approved(temp_database, mocked_add_flow):
    thread_id = f"test-approve-{uuid4()}"

    preview = graph.run_graph("Aggiungi una sneaker", thread_id)

    assert preview["status"] == "awaiting_confirmation"
    assert len(database.get_all_sneakers()) == 0

    result = graph.resume_graph(thread_id=thread_id, approved=True)

    assert result["status"] == "saved"

    sneakers = database.get_all_sneakers()
    assert len(sneakers) == 1

    sneaker = sneakers[0]
    assert sneaker["brand"] == "Adidas"
    assert sneaker["model"] == "Samba OG"
    assert sneaker["colorway"] == "White Black"
    assert sneaker["size"] == 43
    assert sneaker["purchase_price"] == 100


# Sostituisce router ed estrazione LLM per isolare il workflow di modifica.
@pytest.fixture
def mocked_update_flow(monkeypatch):
    def fake_decide_action(text):
        return UpdateSneakerDecision(
            action="update_sneaker",
            query="Adidas Samba OG",
        )

    def fake_parse_sneaker_update_text(text):
        return SneakerUpdate(size=44, size_system="EU")

    monkeypatch.setattr(graph, "decide_action", fake_decide_action)
    monkeypatch.setattr(graph, "parse_sneaker_update_text", fake_parse_sneaker_update_text)


# Verifica che annullare una modifica lasci invariata la sneaker esistente.
def test_update_sneaker_cancelled(temp_database, mocked_update_flow):
    sneaker_id = create_test_sneaker()
    thread_id = f"test-update-cancel-{uuid4()}"

    preview = graph.run_graph("Cambia la taglia delle Adidas Samba OG a 44 EU", thread_id)

    assert preview["status"] == "awaiting_confirmation"
    assert preview["action"] == "update_sneaker"

    result = graph.resume_graph(thread_id=thread_id, approved=False)

    assert result["status"] == "cancelled"

    sneaker = database.get_sneaker_by_id(sneaker_id)
    assert sneaker["size"] == 43


# Verifica che confermare una modifica aggiorni i campi richiesti.
def test_update_sneaker_approved(temp_database, mocked_update_flow):
    sneaker_id = create_test_sneaker()
    thread_id = f"test-update-approve-{uuid4()}"

    preview = graph.run_graph("Cambia la taglia delle Adidas Samba OG a 44 EU", thread_id)

    assert preview["status"] == "awaiting_confirmation"

    result = graph.resume_graph(thread_id=thread_id, approved=True)

    assert result["status"] == "updated"

    sneaker = database.get_sneaker_by_id(sneaker_id)
    assert sneaker["size"] == 44
    assert sneaker["size_system"] == "EU"


# Sostituisce il router per isolare il workflow di eliminazione.
@pytest.fixture
def mocked_delete_flow(monkeypatch):
    def fake_decide_action(text):
        return DeleteSneakerDecision(action="delete_sneaker", query="Adidas Samba OG")

    monkeypatch.setattr(graph, "decide_action", fake_decide_action)


# Verifica che annullare un'eliminazione conservi la sneaker.
def test_delete_sneaker_cancelled(temp_database, mocked_delete_flow):
    sneaker_id = create_test_sneaker()
    thread_id = f"test-delete-cancel-{uuid4()}"

    preview = graph.run_graph("Elimina le Adidas Samba OG", thread_id)

    assert preview["status"] == "awaiting_confirmation"
    assert preview["action"] == "delete_sneaker"

    result = graph.resume_graph(thread_id=thread_id, approved=False)

    assert result["status"] == "cancelled"
    assert database.get_sneaker_by_id(sneaker_id) is not None


# Verifica che confermare un'eliminazione rimuova la sneaker.
def test_delete_sneaker_approved(temp_database, mocked_delete_flow):
    sneaker_id = create_test_sneaker()
    thread_id = f"test-delete-approve-{uuid4()}"

    preview = graph.run_graph("Elimina le Adidas Samba OG", thread_id)

    assert preview["status"] == "awaiting_confirmation"

    result = graph.resume_graph(thread_id=thread_id, approved=True)

    assert result["status"] == "deleted"
    assert database.get_sneaker_by_id(sneaker_id) is None


# Sostituisce router e generazione RAG per isolare il workflow di conoscenza.
@pytest.fixture
def mocked_rag_flow(monkeypatch):
    def fake_decide_action(text):
        return SneakerKnowledgeDecision(action="sneaker_knowledge", query="Jordan Chicago")

    def fake_answer_with_rag(question, top_k=1, retrieval_query=None):
        return {
            "query": question,
            "answer": "La Jordan Chicago è una Air Jordan 1.",
            "sources": [
                {
                    "id": "air-jordan-1-chicago-2015",
                    "title": "Nike Air Jordan 1 Retro High OG Chicago 2015",
                    "score": 0.5,
                }
            ],
        }

    monkeypatch.setattr(graph, "decide_action", fake_decide_action)
    monkeypatch.setattr(graph, "answer_with_rag", fake_answer_with_rag)


# Verifica che il workflow RAG restituisca risposta e fonte attese.
def test_rag_workflow(temp_database, mocked_rag_flow):
    thread_id = f"test-rag-{uuid4()}"

    result = graph.run_graph("Cosa sai della Jordan Chicago?", thread_id)

    assert result["status"] == "completed"
    assert result["action"] == "sneaker_knowledge"
    assert result["response"] == "La Jordan Chicago è una Air Jordan 1."
    assert result["result"]["sources"]
    assert result["result"]["sources"][0]["id"] == "air-jordan-1-chicago-2015"
