from collections import Counter
from typing import Any

from app.llm import parse_sneaker_text
from evals.extraction_cases import EXTRACTION_CASES


# Stampa l'accuratezza aggregata per ciascun campo valutato.
def _print_field_accuracy(field_totals: Counter, field_correct: Counter) -> None:
    print("\nAccuracy by field:")

    for field in sorted(field_totals):
        total = field_totals[field]
        correct = field_correct[field]
        accuracy = correct / total * 100

        print(f"  {field}: {correct}/{total} ({accuracy:.1f}%)")


# Stampa il numero di errori registrati per ciascun campo.
def _print_errors_by_field(errors_by_field: Counter) -> None:
    if not errors_by_field:
        return

    print("\nErrors by field:")

    for field, count in errors_by_field.most_common():
        print(f"  {field}: {count}")


# Stampa il dettaglio dei valori estratti che non coincidono con quelli attesi.
def _print_mismatches(mismatches: list[dict[str, Any]]) -> None:
    if not mismatches:
        print("\nNo mismatches found.")
        return

    print("\nMismatches:")

    for mismatch in mismatches:
        print(f"  [{mismatch['case']}] {mismatch['field']}: expected={mismatch['expected']!r}, actual={mismatch['actual']!r}")


# Esegue tutti i casi di extraction e stampa un report aggregato dei risultati.
def run_evaluation() -> None:
    total_cases = len(EXTRACTION_CASES)
    passed_cases = 0
    total_fields = 0
    correct_fields = 0
    field_totals = Counter()
    field_correct = Counter()
    errors_by_field = Counter()
    mismatches = []

    for case in EXTRACTION_CASES:
        case_name = case["name"]
        user_input = case["input"]
        expected = case["expected"]

        print(f"\nEvaluating: {case_name}")

        try:
            extraction = parse_sneaker_text(user_input)
            actual = extraction.model_dump(mode="json")
        except Exception as error:
            print(f"  ERROR: {error}")

            for field, expected_value in expected.items():
                total_fields += 1
                field_totals[field] += 1
                errors_by_field[field] += 1
                mismatches.append(
                    {
                        "case": case_name,
                        "field": field,
                        "expected": expected_value,
                        "actual": "<extraction error>",
                    }
                )

            continue

        case_passed = True

        for field, expected_value in expected.items():
            total_fields += 1
            field_totals[field] += 1
            actual_value = actual.get(field)

            if actual_value == expected_value:
                correct_fields += 1
                field_correct[field] += 1
                continue

            case_passed = False
            errors_by_field[field] += 1
            mismatches.append(
                {
                    "case": case_name,
                    "field": field,
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )

        if case_passed:
            passed_cases += 1
            print("  PASS")
        else:
            print("  FAIL")

    field_accuracy = correct_fields / total_fields * 100 if total_fields else 0
    case_accuracy = passed_cases / total_cases * 100 if total_cases else 0

    print("\n" + "=" * 60)
    print("EXTRACTION EVALUATION REPORT")
    print("=" * 60)
    print(f"Cases:           {total_cases}")
    print(f"Passed cases:    {passed_cases}")
    print(f"Case accuracy:   {case_accuracy:.1f}%")
    print()
    print(f"Fields:          {total_fields}")
    print(f"Correct fields:  {correct_fields}")
    print(f"Field accuracy:  {field_accuracy:.1f}%")

    _print_field_accuracy(field_totals, field_correct)
    _print_errors_by_field(errors_by_field)
    _print_mismatches(mismatches)


if __name__ == "__main__":
    run_evaluation()
