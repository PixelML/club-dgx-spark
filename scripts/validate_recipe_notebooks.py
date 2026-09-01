#!/usr/bin/env python3
"""Fail closed when a published recipe notebook is incomplete or unsafe."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from build_recipe_results import SUMMARY_FIELDS, summary_rows, validate_run


REQUIRED_SECTIONS = (
    "TL;DR",
    "Requirements",
    "Configure",
    "Preflight",
    "Install",
    "Start",
    "Benchmark",
    "Try your own prompt",
)
PROHIBITED = (
    re.compile(
        r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|"
        r"100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])(?:\.\d{1,3}){2})\b"
    ),
)
PROHIBITED_NOTEBOOK_LOCATIONS = (
    re.compile(r"/tmp/"),
    re.compile(r"\.sglang-api-key"),
    re.compile(r"(?:^|[/\"'])\.env(?:$|[/\"'])"),
)


def validate_recipe(manifest_path: Path) -> list[str]:
    errors: list[str] = []
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in ("title", "status", "hardware", "model", "model_revision", "runtime_pin", "notebook", "chart", "results"):
        if not manifest.get(key):
            errors.append(f"{manifest_path}: missing manifest field {key}")

    notebook_path = root / manifest.get("notebook", "")
    chart_path = root / manifest.get("chart", "")
    result_paths = [root / item for item in manifest.get("results", [])]
    for path in (notebook_path, chart_path, *result_paths):
        if not path.is_file():
            errors.append(f"{manifest_path}: missing {path.relative_to(root)}")
    if not notebook_path.is_file():
        return errors

    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    if notebook.get("nbformat") != 4:
        errors.append(f"{notebook_path}: notebook must use nbformat 4")
    cells = notebook.get("cells", [])
    markdown = "\n".join("".join(cell.get("source", [])) for cell in cells if cell.get("cell_type") == "markdown")
    code = "\n".join("".join(cell.get("source", [])) for cell in cells if cell.get("cell_type") == "code")
    for section in REQUIRED_SECTIONS:
        if section.lower() not in markdown.lower():
            errors.append(f"{notebook_path}: missing section {section}")
    if "curl " not in code or "/v1" not in code:
        errors.append(f"{notebook_path}: final editable curl request is missing")
    if "usage" not in code.lower() or "completion_tokens" not in code:
        errors.append(f"{notebook_path}: usage-token accounting guard is missing")
    if not any(cell.get("outputs") for cell in cells if cell.get("cell_type") == "code"):
        errors.append(f"{notebook_path}: no clean recorded outputs are preserved")
    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]

    def stream_text(cell: dict) -> str:
        return "".join(
            "".join(output.get("text", []))
            for output in cell.get("outputs", [])
            if output.get("output_type") == "stream"
        )

    counts = [cell.get("execution_count") for cell in code_cells]
    if counts != list(range(1, len(code_cells) + 1)):
        errors.append(f"{notebook_path}: code cells are not a fresh top-to-bottom execution")
    if any(not cell.get("outputs") for cell in code_cells):
        errors.append(f"{notebook_path}: every recorded-mode code cell must preserve a concise output")
    if "--fail-with-body" not in code or "jq -e" not in code:
        errors.append(f"{notebook_path}: final curl must fail on HTTP or response-schema errors")
    if "Pillow==11.2.1" not in code:
        errors.append(f"{notebook_path}: chart dependency pin is not enforced")
    configure_output = stream_text(code_cells[0]) if code_cells else ""
    if manifest.get("runtime_pin") not in configure_output:
        errors.append(f"{notebook_path}: recorded configure output does not match runtime_pin")
    if not re.search(r'"executed_at_utc": "\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"', configure_output):
        errors.append(f"{notebook_path}: fresh recorded execution timestamp is missing")
    if code_cells:
        try:
            final_recorded = json.loads(stream_text(code_cells[-1]))
            if not final_recorded.get("response"):
                errors.append(f"{notebook_path}: final recorded response receipt is empty")
            usage = final_recorded.get("usage")
            if not isinstance(usage, dict) or int(usage.get("completion_tokens", 0)) <= 0:
                errors.append(f"{notebook_path}: final recorded usage receipt is missing")
        except (TypeError, ValueError, json.JSONDecodeError):
            errors.append(f"{notebook_path}: final recorded response/usage output is invalid")
    for pattern in PROHIBITED_NOTEBOOK_LOCATIONS:
        if pattern.search(code):
            errors.append(
                f"{notebook_path}: concrete credential/runtime location matched {pattern.pattern}"
            )

    recorded_path = root / "results" / "recorded-run.json"
    summary_path = root / "results" / "summary.csv"
    if recorded_path.is_file() and summary_path.is_file():
        try:
            recorded = json.loads(recorded_path.read_text(encoding="utf-8"))
            validate_run(recorded)
            expected = summary_rows(recorded)
            with summary_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                actual = list(reader)
                if tuple(reader.fieldnames or ()) != SUMMARY_FIELDS:
                    errors.append(f"{summary_path}: summary columns do not match the schema")
            if actual != expected:
                errors.append(f"{summary_path}: summary is stale relative to recorded-run.json")
        except (ValueError, json.JSONDecodeError) as error:
            errors.append(f"{recorded_path}: {error}")
    else:
        errors.append(f"{manifest_path}: recorded-run.json and summary.csv are required")

    chart_spec_path = root / "chart-spec.json"
    if chart_spec_path.is_file():
        chart_spec = json.loads(chart_spec_path.read_text(encoding="utf-8"))
        if any("values" in series for panel in chart_spec.get("panels", []) for series in panel.get("series", [])):
            errors.append(f"{chart_spec_path}: chart values must come only from summary.csv")

    public_text = manifest_path.read_text(encoding="utf-8") + "\n" + notebook_path.read_text(encoding="utf-8")
    for pattern in PROHIBITED:
        if pattern.search(public_text):
            errors.append(f"{manifest_path}: prohibited public identifier matched {pattern.pattern}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path.cwd(), type=Path)
    args = parser.parse_args()
    manifests = sorted(args.root.glob("recipes/*/recipe.json"))
    if not manifests:
        raise SystemExit("no published recipe manifests found")
    errors = [error for manifest in manifests for error in validate_recipe(manifest)]
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"validated {len(manifests)} reproducible recipe notebook(s)")


if __name__ == "__main__":
    main()
