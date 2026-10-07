from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import (
    add_sneaker,
    create_database,
    delete_sneaker,
    get_all_sneakers,
    get_collection_stats,
    get_sneaker_by_id,
    search_sneakers,
)
from .graph import resume_graph, run_graph
from .llm import parse_sneaker_text
from .models import (
    ConfirmationRequest,
    SneakerCreate,
    SneakerExtraction,
    SneakerResponse,
    SneakerTextRequest,
)
from .rag import answer_with_rag, retrieve


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializza il database all'avvio dell'applicazione."""
    create_database()
    yield


app = FastAPI(
    title="Sneakers Collector API",
    description="API per la gestione di una collezione di sneakers.",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def home(request: Request):
    """Renderizza la pagina principale dell'applicazione."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/ai/parse", response_model=SneakerExtraction)
def parse_sneaker(request: SneakerTextRequest):
    """Estrae dati strutturati da una descrizione testuale di una sneaker."""
    try:
        return parse_sneaker_text(request.text)
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error))


@app.post("/ai/chat")
def ai_chat(request: SneakerTextRequest):
    """Avvia un nuovo workflow AI per la richiesta dell'utente."""
    try:
        thread_id = str(uuid4())
        return run_graph(request.text, thread_id)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=502, detail=str(error))


@app.post("/ai/confirm")
def confirm_action(request: ConfirmationRequest):
    """Riprende un workflow AI sospeso dopo la conferma dell'utente."""
    try:
        return resume_graph(thread_id=request.thread_id, approved=request.approved)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=502, detail=str(error))


@app.post("/ai/add-confirm", response_model=SneakerResponse, status_code=status.HTTP_201_CREATED)
def confirm_add_sneaker(sneaker: SneakerCreate):
    """Conferma direttamente l'inserimento di una sneaker tramite API."""
    sneaker_id = add_sneaker(sneaker)
    return get_sneaker_by_id(sneaker_id)


@app.post("/sneakers", response_model=SneakerResponse, status_code=status.HTTP_201_CREATED)
def create_sneaker(sneaker: SneakerCreate):
    """Crea una nuova sneaker nella collezione."""
    sneaker_id = add_sneaker(sneaker)
    return get_sneaker_by_id(sneaker_id)


@app.get("/sneakers", response_model=list[SneakerResponse])
def list_sneakers():
    """Restituisce tutte le sneaker presenti nella collezione."""
    return get_all_sneakers()


@app.get("/sneakers/search", response_model=list[SneakerResponse])
def search(query: str = Query(min_length=1)):
    """Cerca sneaker nella collezione usando una query testuale."""
    return search_sneakers(query)


@app.get("/sneakers/{sneaker_id}", response_model=SneakerResponse)
def get_sneaker(sneaker_id: int):
    """Restituisce una sneaker specifica tramite il suo ID."""
    sneaker = get_sneaker_by_id(sneaker_id)

    if sneaker is None:
        raise HTTPException(status_code=404, detail="Sneaker not found")

    return sneaker


@app.delete("/sneakers/{sneaker_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_sneaker(sneaker_id: int):
    """Elimina una sneaker dalla collezione tramite il suo ID."""
    deleted = delete_sneaker(sneaker_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Sneaker not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/stats")
def stats():
    """Restituisce le statistiche aggregate della collezione."""
    return get_collection_stats()


@app.get("/rag/search")
def rag_search(query: str = Query(min_length=3), top_k: int = Query(default=3, ge=1, le=10)):
    """Recupera i documenti RAG più rilevanti per una query."""
    results = retrieve(query, top_k=top_k)

    return {
        "query": query,
        "results": results,
    }


@app.get("/rag/ask")
def rag_ask(query: str = Query(min_length=3), top_k: int = Query(default=1, ge=1, le=10)):
    """Genera una risposta grounded usando la knowledge base RAG."""
    return answer_with_rag(query, top_k=top_k)
