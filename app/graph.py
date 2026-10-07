import sqlite3
from typing import Any, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .agent import decide_action, execute_action, format_tool_response
from .database import add_sneaker, get_sneaker_by_id
from .llm import parse_sneaker_text, parse_sneaker_update_text
from .models import SneakerCreate, SneakerResponse
from .rag import answer_with_rag
from .tools import (
    remove_sneaker,
    search_collection,
    sneaker_by_id,
    update_sneaker_fields,
)


class AgentState(TypedDict, total=False):
    """Descrive lo stato condiviso tra i nodi del workflow LangGraph."""

    user_text: str
    decision: Any
    result: Any
    response: str
    status: str
    preview: dict
    approved: bool
    updates: dict
    changes: list[dict]


def router_node(state: AgentState):
    """Determina l'azione da eseguire a partire dalla richiesta dell'utente."""
    decision = decide_action(state["user_text"])

    return {"decision": decision}


def tool_node(state: AgentState):
    """Esegue l'azione deterministica associata alla decisione del router."""
    decision = state["decision"]
    result = execute_action(decision)

    return {"result": result}


def formatter_node(state: AgentState):
    """Formatta in linguaggio naturale il risultato prodotto da un tool."""
    decision = state["decision"]
    result = state["result"]
    response = format_tool_response(action=decision.action, result=result)

    return {"response": response}


def unsupported_node(state: AgentState):
    """Restituisce una risposta standard per richieste non supportate."""
    return {
        "response": ("Posso aiutarti con la gestione della tua collezione di sneakers.")
    }


def rag_node(state: AgentState):
    """Genera una risposta grounded usando la knowledge base RAG."""
    decision = state["decision"]
    rag_result = answer_with_rag(question=state["user_text"], retrieval_query=decision.query)

    return {
        "status": "completed",
        "result": {"sources": rag_result["sources"]},
        "response": rag_result["answer"],
    }


def add_preview_node(state: AgentState):
    """Estrae i dati della nuova sneaker e prepara la preview di conferma."""
    extraction = parse_sneaker_text(state["user_text"])

    return {
        "status": "preview",
        "preview": extraction.model_dump(mode="json"),
        "response": ("Controlla i dati estratti prima di confermare l'inserimento.")
    }


def save_sneaker_node(state: AgentState):
    """Salva la sneaker confermata e restituisce il record serializzato."""
    preview_data = {
        key: value
        for key, value in state["preview"].items()
        if value is not None
    }

    sneaker = SneakerCreate.model_validate(preview_data)
    sneaker_id = add_sneaker(sneaker)
    created = get_sneaker_by_id(sneaker_id)
    serialized = SneakerResponse.model_validate(created).model_dump(mode="json")

    return {
        "status": "saved",
        "result": serialized,
        "response": (f"Sneaker aggiunta correttamente con ID {sneaker_id}.")
    }


def update_lookup_node(state: AgentState):
    """Individua la sneaker da modificare e prepara le differenze richieste."""
    decision = state["decision"]
    results = search_collection(decision.query)

    if len(results) == 0:
        return {
            "result": [],
            "status": "not_found",
            "response": ("Non ho trovato nessuna sneaker corrispondente da modificare.")
        }

    if len(results) > 1:
        return {
            "result": results,
            "status": "ambiguous",
            "response": ("Ho trovato più sneakers corrispondenti. Specifica meglio quale vuoi modificare.")
        }

    sneaker = results[0]
    extraction = parse_sneaker_update_text(state["user_text"])
    requested_updates = extraction.model_dump(mode="json", exclude_none=True)

    if not requested_updates:
        return {
            "result": sneaker,
            "status": "no_updates",
            "response": ("Non ho trovato informazioni da modificare.")
        }

    changes = []
    effective_updates = {}

    for field, new_value in requested_updates.items():
        old_value = sneaker.get(field)

        if old_value == new_value:
            continue

        changes.append(
            {
                "field": field,
                "old": old_value,
                "new": new_value,
            }
        )
        effective_updates[field] = new_value

    if not effective_updates:
        return {
            "result": sneaker,
            "status": "no_changes",
            "response": ("I valori indicati sono già presenti sulla sneaker.")
        }

    return {
        "result": sneaker,
        "updates": effective_updates,
        "changes": changes,
        "preview": {
            "sneaker": sneaker,
            "changes": changes,
        },
        "status": "pending_update",
    }


def update_sneaker_node(state: AgentState):
    """Applica alla sneaker le modifiche confermate dall'utente."""
    sneaker = state["result"]
    updates = state["updates"]
    updated_sneaker = update_sneaker_fields(sneaker["id"], updates)

    if updated_sneaker is None:
        return {
            "status": "error",
            "response": ("Non è stato possibile aggiornare la sneaker.")
        }

    return {
        "result": updated_sneaker,
        "status": "updated",
        "response": (f"{updated_sneaker['brand']} {updated_sneaker['model']} è stata aggiornata.")
    }


def delete_lookup_node(state: AgentState):
    """Individua la sneaker da eliminare tramite ID o ricerca testuale."""
    decision = state["decision"]

    if decision.sneaker_id is not None:
        sneaker = sneaker_by_id(decision.sneaker_id)

        if sneaker is None:
            return {
                "result": None,
                "status": "not_found",
                "response": (f"Non ho trovato una sneaker con ID {decision.sneaker_id}.")
            }

        return {
            "result": sneaker,
            "preview": sneaker,
            "status": "pending_delete",
        }

    results = search_collection(decision.query)

    if len(results) == 0:
        return {
            "result": [],
            "status": "not_found",
            "response": ("Non ho trovato nessuna sneaker corrispondente da eliminare.")
        }

    if len(results) > 1:
        return {
            "result": results,
            "status": "ambiguous",
            "response": ("Ho trovato più sneakers corrispondenti. Seleziona quella che vuoi eliminare.")
        }

    sneaker = results[0]

    return {
        "result": sneaker,
        "preview": sneaker,
        "status": "pending_delete",
    }


def delete_sneaker_node(state: AgentState):
    """Elimina la sneaker confermata dall'utente."""
    sneaker = state["preview"]
    sneaker_id = sneaker["id"]
    deleted = remove_sneaker(sneaker_id)

    if not deleted:
        return {
            "status": "error",
            "response": ("Non è stato possibile eliminare la sneaker.")
        }

    return {
        "status": "deleted",
        "response": (f"{sneaker['brand']} {sneaker['model']} è stata eliminata dalla collezione.")
    }


def approval_node(state: AgentState):
    """Interrompe il workflow e richiede la conferma dell'operazione."""
    action = state["decision"].action

    if action == "delete_sneaker":
        question = "Confermi la cancellazione di questa sneaker?"
    elif action == "update_sneaker":
        question = "Confermi le modifiche a questa sneaker?"
    else:
        question = "Confermi l'inserimento di questa sneaker?"

    approved = interrupt(
        {
            "operation": action,
            "question": question,
            "preview": state["preview"],
        }
    )

    return {"approved": bool(approved)}


def cancel_add_node(state: AgentState):
    """Annulla l'operazione in attesa preservando il nome legacy del nodo."""
    action = state["decision"].action

    if action == "delete_sneaker":
        response = "Cancellazione annullata."
    elif action == "update_sneaker":
        response = "Modifica annullata."
    else:
        response = "Inserimento annullato."

    return {
        "status": "cancelled",
        "response": response,
    }


def route_after_decision(state: AgentState):
    """Instrada il workflow verso il nodo coerente con l'azione scelta."""
    action = state["decision"].action

    if action == "add_sneaker":
        return "add_preview"

    if action == "delete_sneaker":
        return "delete_lookup"

    if action == "update_sneaker":
        return "update_lookup"

    if action == "unsupported":
        return "unsupported"

    if action == "sneaker_knowledge":
        return "rag"

    return "tool"


def route_after_approval(state: AgentState):
    """Instrada l'operazione confermata oppure la annulla."""
    if not state["approved"]:
        return "cancel_add"

    action = state["decision"].action

    if action == "add_sneaker":
        return "save_sneaker"

    if action == "delete_sneaker":
        return "delete_sneaker"

    if action == "update_sneaker":
        return "update_sneaker"

    return "cancel_add"


def route_after_delete_lookup(state: AgentState):
    """Prosegue verso la conferma solo quando la cancellazione è univoca."""
    if state["status"] == "pending_delete":
        return "approval"

    return "end"


def route_after_update_lookup(state: AgentState):
    """Prosegue verso la conferma solo quando la modifica è applicabile."""
    if state["status"] == "pending_update":
        return "approval"

    return "end"


checkpoint_connection = sqlite3.connect("data/langgraph_checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(checkpoint_connection)

builder = StateGraph(AgentState)

builder.add_node("router", router_node)
builder.add_node("tool", tool_node)
builder.add_node("formatter", formatter_node)
builder.add_node("add_preview", add_preview_node)
builder.add_node("save_sneaker", save_sneaker_node)
builder.add_node("update_lookup", update_lookup_node)
builder.add_node("update_sneaker", update_sneaker_node)
builder.add_node("delete_lookup", delete_lookup_node)
builder.add_node("delete_sneaker", delete_sneaker_node)
builder.add_node("approval", approval_node)
builder.add_node("cancel_add", cancel_add_node)
builder.add_node("unsupported", unsupported_node)
builder.add_node("rag", rag_node)

builder.add_edge(START, "router")

builder.add_conditional_edges("router", route_after_decision,
    {
        "tool": "tool",
        "add_preview": "add_preview",
        "delete_lookup": "delete_lookup",
        "update_lookup": "update_lookup",
        "unsupported": "unsupported",
        "rag": "rag",
    }
)

builder.add_edge("tool", "formatter")
builder.add_edge("formatter", END)
builder.add_edge("add_preview", "approval")
builder.add_edge("unsupported", END)
builder.add_edge("rag", END)

builder.add_conditional_edges("approval", route_after_approval,
    {
        "save_sneaker": "save_sneaker",
        "delete_sneaker": "delete_sneaker",
        "update_sneaker": "update_sneaker",
        "cancel_add": "cancel_add",
    }
)

builder.add_edge("save_sneaker", END)
builder.add_edge("delete_sneaker", END)
builder.add_edge("update_sneaker", END)
builder.add_edge("cancel_add", END)

builder.add_conditional_edges("delete_lookup", route_after_delete_lookup,
    {
        "approval": "approval",
        "end": END,
    }
)

builder.add_conditional_edges("update_lookup", route_after_update_lookup,
    {
        "approval": "approval",
        "end": END,
    }
)

agent_graph = builder.compile(checkpointer=checkpointer)


def run_graph(text: str, thread_id: str):
    """Avvia un nuovo workflow LangGraph per la richiesta ricevuta."""
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    result = agent_graph.invoke({"user_text": text}, config=config)

    response = {
        "thread_id": thread_id,
        "action": result["decision"].action,
        "response": result.get("response"),
    }

    if "result" in result:
        response["result"] = result["result"]

    if "status" in result:
        response["status"] = result["status"]

    if "preview" in result:
        response["preview"] = result["preview"]

    if "__interrupt__" in result:
        response["status"] = "awaiting_confirmation"
        response["confirmation"] = result["__interrupt__"][0].value

    return response


def resume_graph(thread_id: str, approved: bool):
    """Riprende un workflow sospeso usando la conferma fornita dall'utente."""
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    snapshot = agent_graph.get_state(config)

    if not snapshot.next:
        raise ValueError("Questo workflow non è in attesa di conferma oppure è già stato completato.")

    result = agent_graph.invoke(Command(resume=approved), config=config)

    return {
        "thread_id": thread_id,
        "status": result.get("status"),
        "result": result.get("result"),
        "response": result.get("response"),
    }
