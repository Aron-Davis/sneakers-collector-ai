from typing import TypeVar

import requests
from pydantic import BaseModel, ValidationError

from .models import SneakerExtraction, SneakerUpdate
from .normalization import (
    parse_explicit_condition,
    parse_explicit_date,
    parse_explicit_has_box,
)


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"


SYSTEM_PROMPT = """
You are a structured data extraction system specialized in sneakers.

Your task is to extract sneaker information from the user's message.

Possible fields:

- brand: sneaker manufacturer, for example Nike, Adidas, New Balance, Asics
- model: sneaker model, for example Air Jordan 1, Samba OG, 990v6
- colorway: colors or official colorway name
- style_code: SKU or style code if explicitly provided
- size: numeric shoe size
- size_system: EU, US or UK
- condition: new, like_new, used or worn
- purchase_price: numeric purchase price
- currency: three-letter code such as EUR or USD
- purchase_date: purchase date if explicitly provided
- has_box: whether the original box is present
- notes: additional relevant information explicitly provided by the user

Important rules:

- Extract only information supported by the user's message.
- Do not guess missing fields.
- If information is not provided, return null.
- Never confuse brand, model and colorway.
- Colors belong in colorway.
- Preserve complete colorway names when possible.
- Do not split parts of a colorway into notes.
- "practically new", "like new", "almost new" should map to "like_new".
- "new" should only be used when the item is explicitly described as new or unworn.
- Extract prices even when written with symbols such as €, $, or £.
- € means EUR.
- $ means USD when the context indicates US dollars.
- notes must only contain additional information explicitly provided by the user.
- Do not use notes to explain or justify your extraction.
- Do not add product trivia or external information to notes.
- Follow exactly the provided JSON schema.
- "model" should contain the base sneaker model name only.
- Keep release names, edition names and color descriptors separate from the base model.
- When a base model is followed by a descriptive release or colorway phrase, place that complete phrase in "colorway" instead of extending "model".
- Prefer preserving a shorter canonical base model and a complete colorway rather than absorbing part of the colorway into the model name.

Condition mapping:

- "new": explicitly new, unworn or never used.
- "like_new": used very little or described as almost new, practically new, as good as new, or equivalent expressions.
- "used": normally used, without indications that it is nearly new.
- "worn": heavily used, visibly worn or in poor condition.

Interpret equivalent expressions semantically, including when they are written in languages other than English.

Box information:

- has_box = true only when the user explicitly states that the original box is present.
- has_box = false when the user explicitly states that the box is missing, unavailable, no longer owned, or that the sneakers are without the box.
- has_box = null when the user provides no information about the box.
- Pay attention to negations and semantically equivalent expressions, including expressions written in languages other than English.
"""

UPDATE_SYSTEM_PROMPT = """
You extract only the fields that the user explicitly wants to modify on an existing sneaker.

Rules:

- Extract only the NEW values the user wants to assign.
- Do not extract information that is used only to identify the sneaker.
- Every field that is not being changed must be null.
- Do not guess missing values.
- Do not infer additional changes that the user did not request.

Field rules:

- "size" is the new sneaker size.
- "size_system" is EU, US or UK only when explicitly stated.
- "condition" must be one of: new, like_new, used, worn.
- "purchase_price" is the new purchase price.
- "currency" is the currency explicitly associated with the price.
- "has_box" is true if the user says the original box is present or has been found.
- "has_box" is false if the user says the original box is missing, unavailable or no longer owned.
- "has_box" is null if box information is not being changed.
- "colorway", "style_code", "purchase_date" and "notes" must only be set when the user explicitly wants to change them.

Important:

The sneaker name, brand, model and identifying description are used only to locate the existing sneaker.
Do not copy them into update fields.

Examples:

User:
"Aggiungi la taglia 45 EU alle Adidas Gazelle"

Output meaning:
size = 45
size_system = EU
all other fields = null


User:
"Imposta le Nike Dunk Grey Fog come used"

Output meaning:
condition = used
all other fields = null


User:
"Ho ritrovato la scatola delle Jordan 1 Chicago"

Output meaning:
has_box = true
all other fields = null


User:
"Non ho più la scatola delle Air Max 1"

Output meaning:
has_box = false
all other fields = null


User:
"Le New Balance le ho pagate 180 euro"

Output meaning:
purchase_price = 180 
currency = EUR 
all other fields = null
"""


ModelType = TypeVar("ModelType", bound=BaseModel)


def _build_payload(text: str, system_prompt: str, model_type: type[ModelType]) -> dict:
    """Costruisce il payload Ollama condiviso per le estrazioni strutturate."""
    return {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        "stream": False,
        "format": model_type.model_json_schema(),
        "options": {
            "temperature": 0,
        },
    }


def _request_structured_output(payload: dict, model_type: type[ModelType]) -> ModelType:
    """Invia il payload a Ollama e valida la risposta con il modello Pydantic richiesto."""
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        content = result["message"]["content"]

        return model_type.model_validate_json(content)

    except requests.RequestException as error:
        raise RuntimeError(f"Errore nella comunicazione con Ollama: {error}") from error

    except (KeyError, ValidationError) as error:
        raise RuntimeError(f"Output del modello non valido: {error}") from error


def _apply_explicit_extraction_overrides(text: str, extraction: SneakerExtraction) -> SneakerExtraction:
    """Applica le normalizzazioni deterministiche ai valori espliciti presenti nel testo."""
    explicit_date = parse_explicit_date(text)
    if explicit_date is not None:
        extraction.purchase_date = explicit_date

    explicit_condition = parse_explicit_condition(text)
    if explicit_condition is not None:
        extraction = SneakerExtraction.model_validate(
            {
                **extraction.model_dump(),
                "condition": explicit_condition,
            }
        )

    explicit_has_box = parse_explicit_has_box(text)
    if explicit_has_box is not None:
        extraction = SneakerExtraction.model_validate(
            {
                **extraction.model_dump(),
                "has_box": explicit_has_box,
            }
        )

    return extraction


def parse_sneaker_text(text: str) -> SneakerExtraction:
    """Estrae i dati di una sneaker e applica le normalizzazioni deterministiche esplicite."""
    payload = _build_payload(text=text, system_prompt=SYSTEM_PROMPT, model_type=SneakerExtraction)
    extraction = _request_structured_output(payload=payload, model_type=SneakerExtraction)

    return _apply_explicit_extraction_overrides(text, extraction)


def parse_sneaker_update_text(text: str) -> SneakerUpdate:
    """Estrae esclusivamente i nuovi valori richiesti per aggiornare una sneaker esistente."""
    payload = _build_payload(text=text, system_prompt=UPDATE_SYSTEM_PROMPT, model_type=SneakerUpdate)

    return _request_structured_output(payload=payload, model_type=SneakerUpdate)
