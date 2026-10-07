import re
from datetime import date


MONTHS = {
    # Italiano
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
    # English
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

ISO_DATE_PATTERN = r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"
EUROPEAN_DATE_PATTERN = r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"
MONTH_NAMES_PATTERN = "|".join(MONTHS)
TEXTUAL_DATE_PATTERN = rf"\b(\d{{1,2}})\s+({MONTH_NAMES_PATTERN})\s+(\d{{4}})\b"

WORN_PATTERNS = (
    r"\bmolto consumat[oaie]\b",
    r"\bmolto usurat[oaie]\b",
    r"\bfortemente usurat[oaie]\b",
    r"\bheavily worn\b",
    r"\bvery worn\b",
    r"\bworn out\b",
)

LIKE_NEW_PATTERNS = (
    r"\bcome nuov[oaie]\b",
    r"\bpari al nuovo\b",
    r"\blike new\b",
)

NEW_PATTERNS = (
    r"\bmai indossat[oaie]\b",
    r"\bmai usat[oaie]\b",
    r"\bbrand new\b",
    r"\bdeadstock\b",
)

USED_PATTERNS = (
    r"\busat[oaie]\b",
    r"\bindossat[oaie]\b",
    r"\bused\b",
)

WITHOUT_BOX_PATTERNS = (
    r"\bsenza scatola\b",
    r"\bnon ho (più )?la scatola\b",
    r"\bscatola mancante\b",
    r"\bwithout (the )?box\b",
    r"\bno box\b",
)

WITH_BOX_PATTERNS = (
    r"\bcon scatola\b",
    r"\bho (ancora )?la scatola\b",
    r"\bscatola presente\b",
    r"\bwith (the )?box\b",
    r"\boriginal box included\b",
)


def _create_date(year: int, month: int, day: int) -> date | None:
    """Crea una data valida oppure restituisce None se i valori non sono validi."""
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _matches_any_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    """Verifica se il testo corrisponde ad almeno uno dei pattern indicati."""
    return any(re.search(pattern, text) for pattern in patterns)


def parse_explicit_date(text: str) -> date | None:
    """Estrae una data esplicita dal testo nei formati supportati."""
    normalized_text = text.lower().strip()

    iso_match = re.search(ISO_DATE_PATTERN, normalized_text)
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        return _create_date(year, month, day)

    numeric_match = re.search(EUROPEAN_DATE_PATTERN, normalized_text)
    if numeric_match:
        day, month, year = map(int, numeric_match.groups())
        return _create_date(year, month, day)

    textual_match = re.search(TEXTUAL_DATE_PATTERN, normalized_text)
    if textual_match:
        day = int(textual_match.group(1))
        month = MONTHS[textual_match.group(2)]
        year = int(textual_match.group(3))
        return _create_date(year, month, day)

    return None


def parse_explicit_condition(text: str) -> str | None:
    """Estrae dal testo una condizione della sneaker espressa esplicitamente."""
    normalized_text = text.lower().strip()

    if _matches_any_pattern(normalized_text, WORN_PATTERNS):
        return "worn"

    if _matches_any_pattern(normalized_text, LIKE_NEW_PATTERNS):
        return "like_new"

    if _matches_any_pattern(normalized_text, NEW_PATTERNS):
        return "new"

    if _matches_any_pattern(normalized_text, USED_PATTERNS):
        return "used"

    return None


def parse_explicit_has_box(text: str) -> bool | None:
    """Determina se il testo indica esplicitamente la presenza della scatola."""
    normalized_text = text.lower().strip()

    if _matches_any_pattern(normalized_text, WITHOUT_BOX_PATTERNS):
        return False

    if _matches_any_pattern(normalized_text, WITH_BOX_PATTERNS):
        return True

    return None
