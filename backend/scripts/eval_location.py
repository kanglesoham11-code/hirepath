"""
Evaluate the location resolver against the labelled fixture file.

Prints a confusion table, precision, recall, and every error row.

Usage:
    python -m scripts.eval_location
"""
import csv
import sys
from pathlib import Path

# Ensure backend root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.location_resolver import resolve_location


FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "location_cases.csv"


def main() -> None:
    tp = fp = tn = fn = 0
    errors: list[dict] = []

    with open(FIXTURE, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            text = row["text"].strip()
            expected_accepted = row["expected_accepted"].strip().lower() == "true"
            expected_city = row.get("expected_city", "").strip() or None

            result = resolve_location(text)

            if result.accepted and expected_accepted:
                tp += 1
                # Also check city match if expected_city is specified
                if expected_city and result.city and result.city != expected_city:
                    errors.append({
                        "text": text,
                        "expected": f"accepted (city={expected_city})",
                        "got": f"accepted (city={result.city})",
                        "reason": result.reason,
                        "confidence": result.confidence,
                        "type": "city_mismatch",
                    })
            elif not result.accepted and not expected_accepted:
                tn += 1
            elif result.accepted and not expected_accepted:
                fp += 1
                errors.append({
                    "text": text,
                    "expected": "rejected",
                    "got": f"accepted (city={result.city}, conf={result.confidence})",
                    "reason": result.reason,
                    "confidence": result.confidence,
                    "type": "false_positive",
                })
            else:
                fn += 1
                errors.append({
                    "text": text,
                    "expected": f"accepted (city={expected_city})",
                    "got": f"rejected (reason={result.reason})",
                    "reason": result.reason,
                    "confidence": result.confidence,
                    "type": "false_negative",
                })

    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0

    print("=" * 70)
    print("LOCATION RESOLVER EVALUATION")
    print("=" * 70)
    print(f"\n  Total cases:  {total}")
    print(f"\n  Confusion Matrix:")
    print(f"                 Predicted Accept  Predicted Reject")
    print(f"  Actual Accept       {tp:>5}              {fn:>5}")
    print(f"  Actual Reject       {fp:>5}              {tn:>5}")
    print(f"\n  Precision:    {precision:.4f}  (target >= 0.97)")
    print(f"  Recall:       {recall:.4f}  (target >= 0.90)")
    print(f"  Accuracy:     {accuracy:.4f}")

    if errors:
        print(f"\n{'-' * 70}")
        print(f"  ERRORS ({len(errors)}):")
        print(f"{'-' * 70}")
        for e in errors:
            print(f"  [{e['type']}] \"{e['text']}\"")
            print(f"    Expected: {e['expected']}")
            print(f"    Got:      {e['got']}")
            print()
    else:
        print("\n  [PASS] No errors!")

    print("=" * 70)

    # Return exit code for CI
    if precision < 0.97 or recall < 0.90:
        print(f"\n  [FAILED]: precision={precision:.4f} (>= 0.97), recall={recall:.4f} (>= 0.90)")
        sys.exit(1)
    else:
        print(f"\n  [PASSED]: precision={precision:.4f}, recall={recall:.4f}")
        sys.exit(0)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    main()
