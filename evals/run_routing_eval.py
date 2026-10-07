from collections import Counter
from typing import Any

from app.agent import decide_action
from evals.routing_cases import ROUTING_CASES


# Confronta gli argomenti prodotti dal router con quelli attesi dal caso di eval.
def _collect_argument_errors(decision: Any, expected_arguments: dict[str, Any]) -> list[dict[str, Any]]:
    argument_errors = []

    for field, expected_value in expected_arguments.items():
        actual_value = getattr(decision, field, None)

        if actual_value != expected_value:
            argument_errors.append(
                {
                    "field": field,
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )

    return argument_errors


# Stampa il riepilogo dell'accuratezza per ciascuna action attesa.
def _print_action_summary(expected_counts: Counter, errors_by_expected_action: Counter) -> None:
    print("\nCases by expected action:")

    for action in sorted(expected_counts):
        total = expected_counts[action]
        errors = errors_by_expected_action[action]
        correct = total - errors
        action_accuracy = correct / total * 100 if total else 0

        print(f"  {action}: {correct}/{total} ({action_accuracy:.1f}%)")


# Stampa il dettaglio dei casi in cui routing o argomenti non coincidono con l'atteso.
def _print_mismatches(mismatches: list[dict[str, Any]]) -> None:
    if not mismatches:
        print("\nNo mismatches found.")
        return

    print("\nMismatches:")

    for mismatch in mismatches:
        print(f"  [{mismatch['case']}] expected_action={mismatch['expected_action']!r}, actual_action={mismatch['actual_action']!r}")

        for error in mismatch["argument_errors"]:
            print(f"    {error['field']}: expected={error['expected']!r}, actual={error['actual']!r}")


# Esegue tutti i casi di routing e stampa un report aggregato dei risultati.
def run_evaluation() -> None:
    total_cases = len(ROUTING_CASES)
    correct_cases = 0
    expected_counts = Counter()
    errors_by_expected_action = Counter()
    mismatches = []

    for case in ROUTING_CASES:
        case_name = case["name"]
        user_input = case["input"]
        expected_action = case["expected_action"]
        expected_arguments = case.get("expected_arguments", {})

        print(f"\nEvaluating: {case_name}")
        expected_counts[expected_action] += 1

        try:
            decision = decide_action(user_input)
            actual_action = decision.action
        except Exception as error:
            print(f"  ERROR: {error}")
            errors_by_expected_action[expected_action] += 1
            mismatches.append(
                {
                    "case": case_name,
                    "expected_action": expected_action,
                    "actual_action": "<routing error>",
                    "argument_errors": [],
                }
            )
            continue

        argument_errors = _collect_argument_errors(decision, expected_arguments)
        case_correct = (actual_action == expected_action and not argument_errors)

        if case_correct:
            correct_cases += 1
            print("  PASS")
            continue

        errors_by_expected_action[expected_action] += 1
        mismatches.append(
            {
                "case": case_name,
                "expected_action": expected_action,
                "actual_action": actual_action,
                "argument_errors": argument_errors,
            }
        )
        print("  FAIL")

    accuracy = correct_cases / total_cases * 100 if total_cases else 0

    print("\n" + "=" * 60)
    print("ROUTING EVALUATION REPORT")
    print("=" * 60)
    print(f"Cases:       {total_cases}")
    print(f"Correct:     {correct_cases}")
    print(f"Accuracy:    {accuracy:.1f}%")

    _print_action_summary(expected_counts, errors_by_expected_action)
    _print_mismatches(mismatches)


if __name__ == "__main__":
    run_evaluation()
