import json
import math
from pathlib import Path

import requests


OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

CHAT_MODEL = "qwen2.5:3b"
EMBEDDING_MODEL = "nomic-embed-text-v2-moe"

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "sneakers.json"
MIN_RETRIEVAL_SCORE = 0.20

_documents: list[dict] | None = None
_embeddings: list[list[float]] | None = None


RAG_SYSTEM_PROMPT = """
Sei un assistente specializzato nella conoscenza delle sneakers.

La lingua della risposta deve dipendere esclusivamente dalla lingua della domanda dell'utente, non dalla lingua del contesto recuperato.

Se la domanda è in italiano, rispondi interamente in italiano, anche se il contesto o la fonte sono scritti in inglese.
Non rispondere in inglese a una domanda in italiano.

Rispondi alla domanda dell'utente utilizzando esclusivamente le informazioni contenute nel contesto recuperato.

Regole:

- Non inventare informazioni sulle sneakers.
- Non usare informazioni non supportate dal contesto, anche se fanno parte della tua conoscenza interna.
- Se il contesto non contiene informazioni sufficienti, dichiaralo chiaramente nella lingua dell'utente.
- Sii conciso e fattuale.
- Usa italiano naturale e idiomatico quando l'utente scrive in italiano.
- Usa inglese naturale e idiomatico quando l'utente scrive in inglese.
- Mantieni invariati brand, nomi dei modelli, colorway e style code.
"""


def load_documents() -> list[dict]:
    """Carica i documenti della knowledge base dal file JSON."""
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def document_to_text(document: dict) -> str:
    """Converte un documento sneaker nel testo usato per embedding e contesto RAG."""
    fields = [
        ("Title", document.get("title")),
        ("Brand", document.get("brand")),
        ("Model", document.get("model")),
        ("Colorway", document.get("colorway")),
        ("Style code", document.get("style_code")),
        ("Release date", document.get("release_date")),
        ("Description", document.get("description")),
    ]

    lines = [
        f"{label}: {value}"
        for label, value in fields
        if value is not None
    ]

    return "\n".join(lines)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Genera gli embedding dei testi tramite il modello locale Ollama."""
    payload = {
        "model": EMBEDDING_MODEL,
        "input": texts,
    }

    try:
        response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        embeddings = data["embeddings"]

        if len(embeddings) != len(texts):
            raise RuntimeError("Numero di embeddings diverso dal numero di testi.")

        return embeddings

    except requests.RequestException as error:
        raise RuntimeError(f"Errore nella comunicazione con Ollama embeddings: {error}") from error

    except KeyError as error:
        raise RuntimeError("Risposta embeddings di Ollama non valida.") from error


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Calcola la similarità coseno tra due vettori numerici."""
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def build_index() -> int:
    """Costruisce e memorizza in cache l'indice vettoriale della knowledge base."""
    global _documents
    global _embeddings

    documents = load_documents()
    document_texts = [
        f"search_document: {document_to_text(document)}"
        for document in documents
    ]
    embeddings = embed_texts(document_texts)

    _documents = documents
    _embeddings = embeddings

    return len(documents)


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Recupera i documenti più rilevanti per la query sopra la soglia minima."""
    global _documents
    global _embeddings

    if _documents is None or _embeddings is None:
        build_index()

    query_embedding = embed_texts([f"search_query: {query}"])[0]
    scored_documents = []

    for document, embedding in zip(_documents, _embeddings):
        score = cosine_similarity(query_embedding, embedding)
        scored_documents.append(
            {
                **document,
                "score": round(score, 4),
            }
        )

    scored_documents.sort(key=lambda item: item["score"], reverse=True)

    relevant_documents = [
        document
        for document in scored_documents
        if document["score"] >= MIN_RETRIEVAL_SCORE
    ]

    return relevant_documents[:top_k]


def build_context(documents: list[dict]) -> str:
    """Costruisce il contesto testuale numerato da fornire al modello generativo."""
    context_parts = []

    for index, document in enumerate(documents, start=1):
        document_text = document_to_text(document)
        context_parts.append(f"[Document {index}]\n{document_text}")

    return "\n\n".join(context_parts)


def answer_with_rag(question: str, top_k: int = 1, retrieval_query: str | None = None) -> dict:
    """Genera una risposta grounded usando i documenti recuperati dalla knowledge base."""
    search_query = retrieval_query if retrieval_query else question
    documents = retrieve(search_query, top_k=top_k)

    if not documents:
        return {
            "query": question,
            "answer": ("La knowledge base non contiene informazioni rilevanti per questa domanda."),
            "sources": [],
        }

    context = build_context(documents)
    user_prompt = (
        f"Retrieved context:\n\n"
        f"{context}\n\n"
        f"User question:\n"
        f"{question}\n\n"
        f"Important: answer in the same language as the user question."
    )

    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": RAG_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0,
        },
    }

    try:
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        answer = data["message"]["content"]

        return {
            "query": question,
            "answer": answer,
            "sources": [
                {
                    "id": document["id"],
                    "title": document["title"],
                    "score": document["score"],
                }
                for document in documents
            ],
        }

    except requests.RequestException as error:
        raise RuntimeError(f"Errore nella comunicazione con Ollama: {error}") from error

    except KeyError as error:
        raise RuntimeError("Risposta non valida ricevuta da Ollama.") from error
