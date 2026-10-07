import pytest

from app.agent import decide_action
from evals.routing_cases import ROUTING_CASES


pytestmark = pytest.mark.eval


@pytest.mark.parametrize("case", ROUTING_CASES, ids=lambda case: case["name"])
def test_agent_routing(case):
    """Verifica che il router selezioni l'azione e gli argomenti attesi."""
    decision = decide_action(case["input"])

    assert decision.action == case["expected_action"]

    for field, expected_value in case.get("expected_arguments", {}).items():
        assert getattr(decision, field) == expected_value
