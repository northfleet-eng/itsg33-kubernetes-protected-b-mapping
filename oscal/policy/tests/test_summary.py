"""The control rollup and the Markdown a reader sees."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import summary  # noqa: E402


def ar_with(**rules):
    return {"assessment-results": {"results": [{"observations": [
        {"props": [{"name": "assessment-rule-id", "value": rule}],
         **({"subjects": [{"title": "ApiVersion: v1, Kind: Pod, Namespace: d, Name: x",
                           "props": [{"name": "result", "value": result}, {"name": "reason", "value": "because"}]}]}
            if result else {})}
        for rule, result in rules.items()]}]}}


RULES = [{"id": "a", "description": "A", "controls": ["ac-6"], "note": ""},
         {"id": "b", "description": "B", "controls": ["ac-6", "ac-17.400"], "note": "Cannot see where it connects from."}]
COMPDEF = {"component-definition": {"components": [
    {"title": "Upstream Kubernetes", "control-implementations": [{"implemented-requirements": [
        {"control-id": "ac-6"}, {"control-id": "ac-17.400"}, {"control-id": "sc-8"}]}]},
    {"title": "Containerized workload", "control-implementations": [{"implemented-requirements": [
        {"control-id": "si-10"}]}]},
    {"title": "Kyverno", "type": "validation"}]}}


class ControlVerdict(unittest.TestCase):
    def test_all_pass_is_satisfied(self):
        self.assertEqual(summary.control_verdict(["pass", "pass"]), "satisfied")

    def test_any_fail_is_not_satisfied(self):
        self.assertEqual(summary.control_verdict(["pass", "fail", "none"]), "not satisfied")

    def test_unevaluated_rule_blocks_satisfied(self):
        self.assertEqual(summary.control_verdict(["pass", "none"]), "not evaluated")

    def test_error(self):
        self.assertEqual(summary.control_verdict(["error", "fail"]), "error")


class Render(unittest.TestCase):
    def test_label(self):
        self.assertEqual(summary.label("ac-17.400"), "AC-17(400)")
        self.assertEqual(summary.label("cm-6"), "CM-6")

    def test_failure_is_explained_and_unchecked_controls_listed(self):
        md = summary.render(ar_with(a="pass", b="fail"), RULES, COMPDEF, "noncompliant")
        self.assertIn("| AC-6 | not satisfied |", md)
        self.assertIn("| AC-17(400) | not satisfied |", md)
        self.assertIn("`b` on ApiVersion: v1, Kind: Pod, Namespace: d, Name: x: because", md)
        self.assertIn("Cannot see where it connects from.", md)
        self.assertIn("SC-8, SI-10", md)
        self.assertIn("not an assessment of any system", md)

    def test_satisfied_is_qualified_when_the_evidence_has_limits(self):
        md = summary.render(ar_with(a="pass", b="pass"), RULES, COMPDEF, "compliant")
        self.assertIn("| AC-17(400) | satisfied, with limits (see below) |", md)

    def test_satisfied_without_limits_is_plain(self):
        md = summary.render(ar_with(a="pass"), RULES[:1], COMPDEF, "compliant")
        self.assertIn("| AC-6 | satisfied |", md)

    def test_resources_are_counted_once_per_object(self):
        # Kyverno reports one result per (object, rule inside the policy); count objects.
        subject = {"title": "ApiVersion: v1, Kind: Pod, Namespace: d, Name: x",
                   "props": [{"name": "result", "value": "pass"}, {"name": "reason", "value": "ok"}]}
        ar = {"assessment-results": {"results": [{"observations": [
            {"props": [{"name": "assessment-rule-id", "value": "a"}], "subjects": [subject, subject, subject]}]}]}}
        md = summary.render(ar, RULES[:1], COMPDEF, "compliant")
        self.assertIn("| `a` | AC-6 | pass | 1 |", md)

    def test_rule_with_no_resources_reads_not_evaluated(self):
        md = summary.render(ar_with(a="pass", b=None), RULES, COMPDEF, "compliant")
        self.assertIn("| AC-6 | not evaluated |", md)
        self.assertIn("| `b` | AC-6, AC-17(400) | none | 0 |", md)


if __name__ == "__main__":
    unittest.main()
