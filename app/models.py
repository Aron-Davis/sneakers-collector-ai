from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator


# Rappresenta i valori ammessi per lo stato di conservazione di una sneaker.
class SneakerCondition(str, Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    USED = "used"
    WORN = "worn"


# Definisce i dati richiesti per creare una sneaker nella collezione.
class SneakerCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=150)
    colorway: str | None = None
    style_code: str | None = None
    size: float | None = Field(default=None, gt=0, le=60)
    size_system: Literal["EU", "US", "UK"] = "EU"
    condition: SneakerCondition | None = None
    purchase_price: float | None = Field(default=None, ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    purchase_date: date | None = None
    has_box: bool | None = None
    notes: str | None = Field(default=None, max_length=1000)


# Definisce i campi modificabili di una sneaker esistente.
class SneakerUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    colorway: str | None = None
    style_code: str | None = None
    size: float | None = Field(default=None, gt=0, le=60)
    size_system: Literal["EU", "US", "UK"] | None = None
    condition: SneakerCondition | None = None
    purchase_price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    purchase_date: date | None = None
    has_box: bool | None = Field(
        default=None,
        description=(
            "Whether the original sneaker box is present. "
            "True when the user explicitly says the box is present or has been found. "
            "False when the user explicitly says the box is missing or unavailable. "
            "Null when the user is not changing box information."
        ),
    )
    notes: str | None = Field(default=None, max_length=1000)


# Rappresenta una sneaker completa restituita dalle API.
class SneakerResponse(SneakerCreate):
    id: int
    created_at: datetime


# Rappresenta una richiesta testuale inviata all'assistente.
class SneakerTextRequest(BaseModel):
    text: str = Field(min_length=3, max_length=1000)


# Rappresenta i dati strutturati estratti dal testo dell'utente.
class SneakerExtraction(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    brand: str | None = None
    model: str | None = None
    colorway: str | None = None
    style_code: str | None = None
    size: float | None = Field(default=None, gt=0, le=60)
    size_system: Literal["EU", "US", "UK"] | None = None
    condition: SneakerCondition | None = None
    purchase_price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    purchase_date: date | None = None
    has_box: bool | None = Field(
        default=None,
        description=(
            "Whether the original sneaker box is present. "
            "True if the user explicitly says the box is present. "
            "False if the user explicitly says the box is missing, absent, unavailable, no longer owned, or the sneakers are without a box. "
            "Null only when the user gives no information about the box."
        ),
    )
    notes: str | None = Field(default=None, max_length=1000)


# Rappresenta la decisione di mostrare l'intera collezione.
class ListCollectionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["list_collection"]


# Rappresenta la decisione di cercare sneaker nella collezione.
class SearchCollectionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["search_collection"]
    query: str = Field(min_length=1)


# Rappresenta la decisione di calcolare le statistiche della collezione.
class CollectionStatsDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["collection_stats"]


# Rappresenta la decisione di recuperare una sneaker tramite identificativo.
class SneakerByIdDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["sneaker_by_id"]
    sneaker_id: int = Field(gt=0)


# Rappresenta la decisione di aggiungere una nuova sneaker.
class AddSneakerDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["add_sneaker"]


# Rappresenta la decisione di modificare una sneaker esistente.
class UpdateSneakerDecision(BaseModel):
    action: Literal["update_sneaker"]
    query: str = Field(min_length=1)


# Rappresenta la decisione di eliminare una sneaker tramite query o identificativo.
class DeleteSneakerDecision(BaseModel):
    action: Literal["delete_sneaker"]
    query: str | None = None
    sneaker_id: int | None = Field(default=None, ge=1)

    # Verifica che l'eliminazione disponga di almeno un criterio di identificazione.
    @model_validator(mode="after")
    def validate_target(self):
        if self.query is None and self.sneaker_id is None:
            raise ValueError("delete_sneaker requires query or sneaker_id")

        return self


# Rappresenta la richiesta di conferma per un'operazione con human-in-the-loop.
class ConfirmationRequest(BaseModel):
    thread_id: str
    approved: bool


# Rappresenta la decisione di interrogare la knowledge base sulle sneakers.
class SneakerKnowledgeDecision(BaseModel):
    action: Literal["sneaker_knowledge"]
    query: str = Field(min_length=1)


# Rappresenta una richiesta che non appartiene alle azioni supportate.
class UnsupportedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["unsupported"]


AgentDecision = Annotated[
    Union[
        ListCollectionDecision,
        SearchCollectionDecision,
        CollectionStatsDecision,
        SneakerByIdDecision,
        AddSneakerDecision,
        DeleteSneakerDecision,
        UpdateSneakerDecision,
        UnsupportedDecision,
        SneakerKnowledgeDecision,
    ],
    Field(discriminator="action"),
]

agent_decision_adapter = TypeAdapter(AgentDecision)
