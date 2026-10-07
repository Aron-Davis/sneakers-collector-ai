import re

import pytest

from app.rag import answer_with_rag
from evals.rag_generation_cases import RAG_GENERATION_CASES

YEAR_PATTERN = r"\b(?:19|20)\d{2}\b"
OUT_OF_DOMAIN_RESPONSE = ("La knowledge base non contiene informazioni rilevanti per questa domanda.")


# Verifica che la generazione RAG usi la source corretta e resti grounded sui fatti attesi.
@pytest.mark.eval
@pytest.mark.parametrize("case", RAG_GENERATION_CASES, ids=lambda case: case["name"])
def test_rag_grounded_generation(case):
    result = answer_with_rag(question=case["question"], retrieval_query=case["retrieval_query"], top_k=1)

    assert result["sources"], "Nessuna source restituita."
    assert result["sources"][0]["id"] == case["expected_source"]

    answer = result["answer"]

    for expected_value in case["expected_contains"]:
        assert expected_value in answer, (
            f"Valore atteso {expected_value!r} non trovato nella risposta: {answer!r}")

    if case["must_not_contain_year"]:
        assert not re.findall(YEAR_PATTERN, answer), (f"La risposta sembra aver inventato una data: {answer!r}")


# Verifica la risposta deterministica quando la domanda è fuori dominio.
@pytest.mark.eval
def test_rag_out_of_domain():
    result = answer_with_rag(question="Qual è la capitale della Francia?", top_k=1)

    assert result["sources"] == []
    assert result["answer"] == OUT_OF_DOMAIN_RESPONSE
