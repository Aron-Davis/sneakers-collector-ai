from datetime import date

import pytest

from app.normalization import (
    parse_explicit_condition,
    parse_explicit_date,
    parse_explicit_has_box,
)


DATE_CASES = [
    (
        "italian_text_date",
        "Comprate il 15 gennaio 2026 per 130 euro.",
        date(2026, 1, 15),
    ),
    (
        "english_text_date",
        "Purchased on 15 January 2026.",
        date(2026, 1, 15),
    ),
    (
        "numeric_date",
        "Comprate il 15/01/2026.",
        date(2026, 1, 15),
    ),
    (
        "iso_date",
        "Purchase date: 2026-01-15",
        date(2026, 1, 15),
    ),
    (
        "missing_date",
        "Nike Dunk Low taglia 44.",
        None,
    ),
    (
        "invalid_date",
        "Comprate il 31 febbraio 2026.",
        None,
    ),
]

CONDITION_CASES = [
    (
        "worn_italian",
        "Nike Dunk molto consumate",
        "worn",
    ),
    (
        "worn_english",
        "The sneakers are heavily worn",
        "worn",
    ),
    (
        "like_new",
        "Sono praticamente come nuove",
        "like_new",
    ),
    (
        "used",
        "Scarpe usate normalmente",
        "used",
    ),
    (
        "condition_not_explicit",
        "Nike Dunk Low Grey Fog taglia 44",
        None,
    ),
]

BOX_CASES = [
    (
        "without_box_italian",
        "Nike Dunk molto consumate e senza scatola",
        False,
    ),
    (
        "without_box_italian_long",
        "Le ho usate parecchio e non ho più la scatola",
        False,
    ),
    (
        "with_box_italian",
        "Adidas Samba con scatola",
        True,
    ),
    (
        "without_box_english",
        "Used sneakers without the box",
        False,
    ),
    (
        "box_not_mentioned",
        "Nike Dunk Low Grey Fog taglia 44",
        None,
    ),
]


# Verifica il parsing deterministico delle date esplicite supportate.
@pytest.mark.parametrize(("case_name", "text", "expected"), DATE_CASES, ids=[case[0] for case in DATE_CASES])
def test_parse_explicit_date(case_name, text, expected):
    assert parse_explicit_date(text) == expected


# Verifica la normalizzazione delle condizioni esplicitamente dichiarate.
@pytest.mark.parametrize(("case_name", "text", "expected"), CONDITION_CASES, ids=[case[0] for case in CONDITION_CASES])
def test_parse_explicit_condition(case_name, text, expected):
    assert parse_explicit_condition(text) == expected


# Verifica il riconoscimento esplicito della presenza o assenza della scatola.
@pytest.mark.parametrize(("case_name", "text", "expected"), BOX_CASES, ids=[case[0] for case in BOX_CASES])
def test_parse_explicit_has_box(case_name, text, expected):
    assert parse_explicit_has_box(text) is expected
