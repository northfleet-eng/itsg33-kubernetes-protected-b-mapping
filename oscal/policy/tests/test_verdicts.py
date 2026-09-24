"""Rule verdicts from assessment results, and the oracle comparison."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_verdicts  # noqa: E402
from verdicts import rule_verdicts, verdict_of  # noqa: E402


def obs(rule, *results):
    return {"props": [{"name": "assessment-rule-id", "value": rule}],
            "subjects": [{"title": f"Kind: Pod, Name: p{i}", "props": [{"name": "result", "value": r},
                                                                      {"name": "reason", "value": "why"}]}
                         for i, r in enumerate(results)]}


class VerdictOf(unittest.TestCase):
    def test_nothing_evaluated_is_none_never_pass(self):
        self.assertEqual(verdict_of([]), "none")

    def test_skip_alone_is_none(self):
        self.assertEqual(verdict_of(["skip", "skip"]), "none")

    def test_pass_with_skips_is_pass(self):
        self.assertEqual(verdict_of(["pass", "skip"]), "pass")

    def test_any_fail_is_fail(self):
        self.assertEqual(verdict_of(["pass", "fail"]), "fail")

    def test_warn_counts_as_fail(self):
        self.assertEqual(verdict_of(["pass", "warn"]), "fail")

    def test_error_wins(self):
        self.assertEqual(verdict_of(["fail", "error"]), "error")


class RuleVerdicts(unittest.TestCase):
    def test_observation_without_subjects_is_none(self):
        ar = {"assessment-results": {"results": [{"observations": [
            {"props": [{"name": "assessment-rule-id", "value": "r"}]}]}]}}
        self.assertEqual(rule_verdicts(ar)["r"]["verdict"], "none")

    def test_rules_are_keyed_by_id(self):
        ar = {"assessment-results": {"results": [{"observations": [obs("a", "pass"), obs("b", "fail")]}]}}
        v = rule_verdicts(ar)
        self.assertEqual((v["a"]["verdict"], v["b"]["verdict"]), ("pass", "fail"))
        self.assertEqual(v["b"]["subjects"][0], ("Kind: Pod, Name: p0", "fail", "why"))


class Compare(unittest.TestCase):
    def test_match(self):
        self.assertEqual(check_verdicts.compare({"a": "pass"}, {"a": {"verdict": "pass"}}), [])

    def test_mismatch_missing_and_unexpected(self):
        problems = check_verdicts.compare({"a": "pass", "b": "fail"},
                                          {"a": {"verdict": "fail"}, "c": {"verdict": "pass"}})
        self.assertEqual(problems, ["a: expected pass, got fail", "b: expected fail, got missing",
                                    "c: not in expected.json"])


class UnknownSample(unittest.TestCase):
    def test_a_sample_without_expectations_is_reported_not_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            exp = Path(tmp) / "expected.json"
            exp.write_text(json.dumps({"compliant": {"a": "pass"}}))
            ar = Path(tmp) / "ar.json"
            ar.write_text(json.dumps({"assessment-results": {"results": [{"observations": [obs("a", "fail")]}]}}))
            out = io.StringIO()
            with redirect_stdout(out):
                check_verdicts.main(str(exp), "mine", str(ar))
        self.assertIn("mine: no entry in expected.json; verdicts not checked", out.getvalue())

    def test_an_error_fails_even_without_expectations(self):
        with tempfile.TemporaryDirectory() as tmp:
            exp = Path(tmp) / "expected.json"
            exp.write_text(json.dumps({"compliant": {"a": "pass"}}))
            ar = Path(tmp) / "ar.json"
            ar.write_text(json.dumps({"assessment-results": {"results": [{"observations": [obs("a", "error")]}]}}))
            err = io.StringIO()
            with self.assertRaises(SystemExit) as ctx, redirect_stdout(io.StringIO()), redirect_stderr(err):
                check_verdicts.main(str(exp), "mine", str(ar))
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIn("mine: rules errored: a", err.getvalue())


if __name__ == "__main__":
    unittest.main()
