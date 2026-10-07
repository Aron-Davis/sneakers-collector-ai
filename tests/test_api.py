from fastapi.testclient import TestClient

import app.main as main


# Verifica che la chat AI restituisca la preview di una nuova sneaker.
def test_ai_chat_returns_preview(temp_database, monkeypatch):
    # Simula il workflow LangGraph fino alla richiesta di conferma.
    def fake_run_graph(text, thread_id):
        return {
            "thread_id": thread_id,
            "action": "add_sneaker",
            "status": "awaiting_confirmation",
            "preview": {
                "brand": "Adidas",
                "model": "Samba OG",
                "size": 43,
            },
            "response": "Controlla i dati estratti prima di confermare.",
        }

    monkeypatch.setattr(main, "run_graph", fake_run_graph)

    with TestClient(main.app) as client:
        response = client.post("/ai/chat", json={"text": "Aggiungi delle Adidas Samba OG"})

    assert response.status_code == 200

    data = response.json()

    assert data["action"] == "add_sneaker"
    assert data["status"] == "awaiting_confirmation"
    assert data["preview"]["brand"] == "Adidas"
    assert data["preview"]["model"] == "Samba OG"
    assert isinstance(data["thread_id"], str)
    assert len(data["thread_id"]) > 0


# Verifica che l'endpoint di conferma gestisca correttamente l'annullamento.
def test_ai_confirm_cancelled(temp_database, monkeypatch):
    # Simula la ripresa del workflow con conferma negativa.
    def fake_resume_graph(thread_id, approved):
        assert thread_id == "test-thread-123"
        assert approved is False

        return {
            "thread_id": thread_id,
            "status": "cancelled",
            "result": None,
            "response": ("Inserimento annullato. La collezione non è stata modificata."),
        }

    monkeypatch.setattr(main, "resume_graph", fake_resume_graph)

    with TestClient(main.app) as client:
        response = client.post("/ai/confirm", json={"thread_id": "test-thread-123", "approved": False})

    assert response.status_code == 200

    data = response.json()

    assert data["thread_id"] == "test-thread-123"
    assert data["status"] == "cancelled"
    assert data["result"] is None


# Verifica che la chat AI rifiuti richieste testuali troppo corte.
def test_ai_chat_rejects_invalid_text(temp_database):
    with TestClient(main.app) as client:
        response = client.post("/ai/chat", json={"text": "a"})

    assert response.status_code == 422


# Verifica che la conferma AI richieda esplicitamente il campo approved.
def test_ai_confirm_requires_approved(temp_database):
    with TestClient(main.app) as client:
        response = client.post("/ai/confirm", json={"thread_id": "test-thread-123"})

    assert response.status_code == 422
