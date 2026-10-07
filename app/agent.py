import requests
from pydantic import ValidationError

from .models import (
    AgentDecision,
    agent_decision_adapter,
)
from .tools import (
    list_collection,
    search_collection,
    collection_stats,
    sneaker_by_id,
)


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"


AGENT_PROMPT = """
You are the routing component of a sneaker collection application.

Your only task is to select exactly one action based on the user's request.

Available actions:

1. list_collection

Use ONLY when the user wants to see the entire collection without any filtering criteria.

Examples:
- "Show me my collection"
- "List all my sneakers"
- "Fammi vedere tutta la mia collezione"

Output:
{"action": "list_collection"}


2. search_collection

Use whenever the user wants a subset of the collection based on brand, model, colorway or style code.

Examples:
- "Show me all my Nike sneakers"
- "Mostrami tutte le Nike che possiedo"
- "Find my Jordan sneakers"
- "Show me the red sneakers"
- "Do I own any Adidas Samba?"

The query must contain the relevant search term.

Output:
{
  "action": "search_collection",
  "query": "Nike"
}


3. collection_stats

Use for questions about collection statistics, such as:
- number of sneakers
- total spending
- number of brands
- average purchase price

Examples:
- "How many sneakers do I own?"
- "Quante sneakers ho?"
- "Quanto ho speso in totale?"

Output:
{"action": "collection_stats"}


4. sneaker_by_id

Use only when the user explicitly refers to a sneaker database ID.

Examples:
- "Show me sneaker with ID 1"
- "Mostrami la sneaker con ID 1"

Output:
{
  "action": "sneaker_by_id",
  "sneaker_id": 1
}

5. add_sneaker

Use when the user wants to add, insert or register a sneaker in their collection.

Examples:
- "Add my Jordan 4 to the collection"
- "Aggiungi delle Jordan 4 taglia 44"
- "Ho comprato delle Air Max 1 e voglio inserirle"

Output:
{"action": "add_sneaker"}

6. delete_sneaker:
  Use when the user explicitly wants to remove or delete a sneaker from their collection.
  Extract into "query" the sneaker description needed to identify it.
  Do not use this action when the user is only asking to view or search for a sneaker.

  "Elimina le Adidas Superstar" -> {"action": "delete_sneaker", "query": "Adidas Superstar"}

  "Rimuovi le Jordan 1 Chicago dalla collezione" -> {"action": "delete_sneaker", "query": "Jordan 1 Chicago"}

  "Cancella le Nike Dunk Low" -> {"action": "delete_sneaker", "query": "Nike Dunk Low"}

  When the user identifies a sneaker by its database ID, put the numeric ID in sneaker_id and set query to null.

 Examples:

 "Elimina la Puma Test Model" -> {"action": "delete_sneaker", "query": "Puma Test Model", "sneaker_id": null}

 "Elimina la sneaker con ID 14" -> {"action": "delete_sneaker", "query": null, "sneaker_id": 14}

7. update_sneaker:
  Use when the user wants to modify, correct, add or change information about a sneaker already present in the collection.

  Put in "query" only the description needed to identify the existing sneaker.

  Do not include the new values being assigned in the query.

  IMPORTANT DISTINCTION BETWEEN add_sneaker AND update_sneaker:

- add_sneaker means adding a NEW PAIR of sneakers to the collection.
- update_sneaker means modifying, completing, correcting or adding information to a sneaker that already exists in the collection.

The verb "add" / "aggiungi" alone does NOT imply add_sneaker.

Determine WHAT is being added:

- "Aggiungi delle Puma Test Model alla collezione" -> add_sneaker

- "Aggiungi il colore nero alle Puma Test Model" -> update_sneaker
  query = "Puma Test Model"

- "Aggiungi la taglia 45 alle Adidas Gazelle" -> update_sneaker
  query = "Adidas Gazelle"

- "Aggiungi il codice prodotto alle Jordan 1 Chicago" -> update_sneaker 
  query = "Jordan 1 Chicago"

- "Aggiungi che hanno la scatola originale" -> update_sneaker

General rule:
If the user is adding or changing an ATTRIBUTE of a named sneaker, use update_sneaker.

Use add_sneaker only when the object being added is the sneaker/pair itself.

  Examples:
  "Aggiungi la taglia 45 EU alle Adidas Gazelle" -> {"action": "update_sneaker", "query": "Adidas Gazelle"}

  "Imposta le Nike Dunk Grey Fog come used" -> {"action": "update_sneaker", "query": "Nike Dunk Grey Fog"}

  "Ho ritrovato la scatola delle Jordan 1 Chicago" -> {"action": "update_sneaker", "query": "Jordan 1 Chicago"}

8. unsupported

Use when the request does not concern the sneaker collection.

Examples:
- "What is the capital of Japan?"
- "Qual è la capitale del Giappone?"

Output:
{"action": "unsupported"}

9. sneaker_knowledge:
  Use when the user asks for general factual information about a sneaker model, release, colorway, style code, history or other sneaker knowledge.

  Use this action for knowledge about sneakers in general, not for information about the user's personal collection.

  Put the sneaker-related question or description in "query".

Examples:

"Cosa sai della Jordan Chicago?" -> {"action": "sneaker_knowledge", "query": "Jordan Chicago"}

"Parlami delle Air Max Anniversary Red" -> {"action": "sneaker_knowledge", "query": "Air Max Anniversary Red"}

"Qual è lo style code della Dunk Panda?" -> {"action": "sneaker_knowledge", "query": "Dunk Panda"}

IMPORTANT:

"Ho delle Jordan Chicago?" -> search_collection

"Cosa sai della Jordan Chicago?" -> sneaker_knowledge

"Quanto ho pagato le mie Jordan?" -> search_collection / collection data

"Quando è uscita la Jordan Chicago?" -> sneaker_knowledge


Important rules:

- list_collection must NEVER be used when the user specifies a brand, model, colorway or style code.
- If the user specifies any filtering criterion, use search_collection.
- Do not answer the user's question.
- Do not invent database information.
- Do not include fields that do not belong to the selected action.
- Follow exactly the provided JSON schema.

IMPORTANT DISTINCTION BETWEEN search_collection AND update_sneaker:

- search_collection is used when the user only wants to find, show, locate or inspect an existing sneaker.
- update_sneaker is used only when the user explicitly wants to change, add, correct or set information on an existing sneaker.

A field mentioned in the request does not automatically mean that the user wants to modify that field.

Examples:

"Trova la sneaker con style code CW2288-111" -> {"action": "search_collection", "query": "CW2288-111"}

"Mostrami le sneakers con style code CW2288-111" -> {"action": "search_collection", "query": "CW2288-111"}

"Imposta lo style code CW2288-111 sulle Air Max" -> {"action": "update_sneaker", "query": "Air Max"}

"Aggiungi lo style code CW2288-111 alle Air Max" -> {"action": "update_sneaker", "query": "Air Max"}

Important distinction between add_sneaker and update_sneaker:

- add_sneaker means the user wants to create a NEW sneaker record in the collection.
- If the user says "aggiungi", "add", "inserisci", or similar and then describes a sneaker with attributes such as brand, model, size, condition, price, or box, classify it as add_sneaker.
- A sneaker may already exist in the collection with the same brand or model. This does NOT turn an add request into an update request. Collectors may own multiple pairs of the same sneaker.

- update_sneaker means the user wants to CHANGE one or more fields of an EXISTING sneaker record.
- Use update_sneaker only when the user clearly refers to an existing sneaker and asks to modify, change, set, correct, or add a property to that record.

Examples:

"Aggiungi delle Adidas Samba OG taglia 43 EU" -> add_sneaker

"Aggiungi delle Adidas Samba OG taglia 43 EU, nuove, con scatola" -> add_sneaker

"Add a pair of Nike Dunk Low size 44" -> add_sneaker

"Cambia la taglia delle Adidas Samba OG a 44 EU" -> update_sneaker

"Modifica le Adidas Samba OG e imposta la taglia a 44 EU" -> update_sneaker

"Aggiungi il colore nero alle mie Adidas Samba OG" -> update_sneaker

General rule:
If the user is asking WHICH sneaker has a property, use search_collection.
If the user is asking to CHANGE that property, use update_sneaker.
"""

def decide_action(text: str) -> AgentDecision:
    """Determina l'azione da eseguire in base alla richiesta dell'utente."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": AGENT_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        "stream": False,
        "format": agent_decision_adapter.json_schema(),
        "options": {
            "temperature": 0
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)

        response.raise_for_status()

        result = response.json()
        content = result["message"]["content"]

        return agent_decision_adapter.validate_json(content)

    except requests.RequestException as error:
        raise RuntimeError(f"Errore nella comunicazione con Ollama: {error}") from error

    except (KeyError, ValidationError) as error:
        raise RuntimeError(f"Decisione dell'agente non valida: {error}") from error


def execute_action(decision: AgentDecision):
    """Esegue l'azione deterministica associata alla decisione dell'agente."""
    if decision.action == "list_collection":
        return list_collection()

    if decision.action == "search_collection":
        return search_collection(decision.query)

    if decision.action == "collection_stats":
        return collection_stats()

    if decision.action == "sneaker_by_id":
        return sneaker_by_id(decision.sneaker_id)

    if decision.action == "unsupported":
        return {
            "message": ("Posso aiutarti con la gestione della tua collezione di sneakers.")
        }

    raise ValueError(f"Azione non supportata: {decision.action}")


def format_amount(value: float) -> str:
    """Formatta un importo rimuovendo gli zeri decimali non necessari."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def format_tool_response(action: str, result) -> str:
    """Converte il risultato di un tool in una risposta testuale deterministica."""
    if action == "collection_stats":
        total_pairs = result["total_pairs"]
        total_brands = result["total_brands"]

        response = (f"Hai {total_pairs} sneakers nella tua collezione di {total_brands} brand.")

        spending = result.get("spending_by_currency", [])

        if spending:
            parts = []

            for item in spending:
                total_spent = format_amount(item["total_spent"])
                average_price = format_amount(item["average_price"])

                parts.append(f"{total_spent} {item['currency']} (media {average_price} {item['currency']})")

            response += " Spesa: " + ", ".join(parts) + "."

        return response

    if action == "search_collection":
        if not result:
            return "Non ho trovato sneakers corrispondenti alla ricerca."

        sneakers = []

        for sneaker in result:
            name = f"{sneaker['brand']} {sneaker['model']}"

            if sneaker.get("colorway"):
                name += f" {sneaker['colorway']}"

            sneakers.append(name)

        return (f"Ho trovato {len(result)} sneakers: " + "; ".join(sneakers) + ".")

    if action == "list_collection":
        if not result:
            return "La tua collezione è vuota."

        sneakers = []

        for sneaker in result:
            name = f"{sneaker['brand']} {sneaker['model']}"

            if sneaker.get("colorway"):
                name += f" {sneaker['colorway']}"

            sneakers.append(name)

        return (f"Hai {len(result)} sneakers nella collezione: " + "; ".join(sneakers) + ".")

    if action == "sneaker_by_id":
        if not result:
            return "Non ho trovato una sneaker con questo ID."

        response = (f"La sneaker con ID {result['id']} è una {result['brand']} {result['model']}")

        if result.get("colorway"):
            response += f" {result['colorway']}"

        if result.get("size"):
            response += (f", taglia {result['size']} {result['size_system']}")

        response += "."

        return response

    return "Operazione completata."


