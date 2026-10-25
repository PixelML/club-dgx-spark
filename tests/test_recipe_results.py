from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_recipe_results.py"
SPEC = importlib.util.spec_from_file_location("build_recipe_results", MODULE_PATH)
assert SPEC and SPEC.loader
RESULTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESULTS)


class RecipeResultsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.recipe = ROOT / "recipes" / "qwen3.8-flash-next-sglang"
        self.run = json.loads(
            (self.recipe / "results" / "recorded-run.json").read_text(encoding="utf-8")
        )

    def test_recorded_run_is_valid_and_uses_authoritative_tokens(self) -> None:
        RESULTS.validate_run(self.run)
        rows = RESULTS.summary_rows(self.run)
        self.assertEqual([row["x"] for row in rows[:4]], ["1", "4", "8", "16"])
        self.assertEqual(rows[4]["prompt_tokens"], "1053")
        self.assertEqual(rows[6]["prompt_tokens"], "16407")
        self.assertIn("usage.prompt_tokens", rows[6]["token_basis"])

    def test_live_jsonl_parser_rejects_missing_concurrency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decode = root / "decode.jsonl"
            prefill = root / "prefill.jsonl"
            decode.write_text(
                json.dumps({"benchmark": self.run["decode"][0]}) + "\n",
                encoding="utf-8",
            )
            prefill.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "decode concurrency"):
                RESULTS.run_from_jsonl(decode, prefill, "public evidence")

    def test_live_jsonl_parser_rebuilds_the_recorded_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decode = root / "decode.jsonl"
            prefill = root / "prefill.jsonl"
            decode.write_text(
                "\n".join(
                    json.dumps({"benchmark": item}) for item in self.run["decode"]
                )
                + "\n",
                encoding="utf-8",
            )
            prefill_records = []
            for group in self.run["prefill"]:
                prefill_records.extend(
                    (
                        {"samples": group["samples"]},
                        {
                            "summary": {
                                "target_prompt_tokens": group[
                                    "target_prompt_tokens"
                                ]
                            }
                        },
                    )
                )
            prefill.write_text(
                "\n".join(json.dumps(record) for record in prefill_records) + "\n",
                encoding="utf-8",
            )
            parsed = RESULTS.run_from_jsonl(decode, prefill, "public evidence")
            self.assertEqual(
                RESULTS.summary_rows(parsed), RESULTS.summary_rows(self.run)
            )

    def test_rate_mismatch_fails_closed(self) -> None:
        altered = json.loads(json.dumps(self.run))
        altered["decode"][0]["aggregate_tps"] = 999
        with self.assertRaisesRegex(ValueError, "decode tok/s"):
            RESULTS.validate_run(altered)


if __name__ == "__main__":
    unittest.main()
