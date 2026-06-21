import argparse
import json
from pathlib import Path
from typing import Any

from evals.schemas import EvalSuiteResult, ExtractionEvalCase, QAEvalCase
from evals.scorers import score_extraction_case, score_qa_case, suite_result

DEFAULT_QA_DATASET = Path("evals/datasets/golden_qa.json")
DEFAULT_EXTRACTION_DATASET = Path("evals/datasets/golden_extraction.json")
DEFAULT_OUTPUT_PATH = Path("evals/reports/latest.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local RAG platform evals.")
    parser.add_argument(
        "--qa-dataset",
        default=str(DEFAULT_QA_DATASET),
        help="Path to golden QA dataset.",
    )
    parser.add_argument(
        "--extraction-dataset",
        default=str(DEFAULT_EXTRACTION_DATASET),
        help="Path to golden extraction dataset.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to write eval report JSON.",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=1.0,
        help="Fail if overall score is below this threshold.",
    )

    args = parser.parse_args()

    qa_cases = _load_qa_cases(Path(args.qa_dataset))
    extraction_cases = _load_extraction_cases(Path(args.extraction_dataset))

    qa_result = suite_result(
        suite_name="golden_qa",
        case_results=[score_qa_case(case) for case in qa_cases],
    )
    extraction_result = suite_result(
        suite_name="golden_extraction",
        case_results=[score_extraction_case(case) for case in extraction_cases],
    )

    suite_results = [qa_result, extraction_result]
    overall_score = _overall_score(suite_results)
    passed = all(result.passed for result in suite_results)

    report = {
        "passed": passed,
        "overall_score": overall_score,
        "suites": [result.model_dump(mode="json") for result in suite_results],
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    _print_report(report)

    if overall_score < args.fail_under:
        raise SystemExit(1)


def _load_qa_cases(path: Path) -> list[QAEvalCase]:
    data = _load_json(path)

    return [QAEvalCase.model_validate(item) for item in data]


def _load_extraction_cases(path: Path) -> list[ExtractionEvalCase]:
    data = _load_json(path)

    return [ExtractionEvalCase.model_validate(item) for item in data]


def _load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _overall_score(results: list[EvalSuiteResult]) -> float:
    total_cases = sum(result.total_cases for result in results)

    if total_cases == 0:
        return 0.0

    weighted_score = sum(result.score * result.total_cases for result in results)

    return weighted_score / total_cases


def _print_report(report: dict[str, Any]) -> None:
    print("Evaluation report")
    print("=================")
    print(f"Overall score: {report['overall_score']:.2f}")
    print(f"Passed: {report['passed']}")
    print("")

    for suite in report["suites"]:
        print(
            f"{suite['suite_name']}: "
            f"{suite['passed_cases']}/{suite['total_cases']} passed "
            f"(score={suite['score']:.2f})"
        )

        for case in suite["case_results"]:
            status = "PASS" if case["passed"] else "FAIL"
            print(f"  [{status}] {case['id']}")

            for error in case["errors"]:
                print(f"    - {error}")

    print("")
    print(f"Report written to: {DEFAULT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
