import pytest

from app.rag import retrieve
from evals.retrieval_cases import RETRIEVAL_CASES


@pytest.mark.eval
@pytest.mark.parametrize("case", RETRIEVAL_CASES, ids=lambda case: case["name"])
def test_rag_retrieval(case):
    """Verifica che il retrieval restituisca come primo risultato il documento atteso."""
    results = retrieve(case["query"], top_k=1)

    assert results, f"Nessun documento recuperato per query: {case['query']}"
    assert results[0]["id"] == case["expected_id"]
