import pytest

from app.llm import parse_sneaker_text
from evals.extraction_cases import EXTRACTION_CASES


pytestmark = pytest.mark.eval


@pytest.mark.parametrize("case", EXTRACTION_CASES, ids=lambda case: case["name"])
def test_sneaker_extraction(case):
    """Verifica che l'estrazione LLM restituisca i campi attesi per ogni caso di valutazione."""
    extraction = parse_sneaker_text(case["input"])
    actual = extraction.model_dump(mode="json")

    for field, expected_value in case["expected"].items():
        assert actual[field] == expected_value
