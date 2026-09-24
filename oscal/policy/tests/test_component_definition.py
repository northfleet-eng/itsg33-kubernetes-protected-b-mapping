"""rules.csv validation and the rule props the component-definition builder emits."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

OSCAL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(OSCAL / "scripts"))
import build_component_definition as bcd  # noqa: E402

RULES = OSCAL / "policy" / "src" / "rules.csv"
POLICIES = OSCAL / "policy" / "kyverno" / "policies"
MAPPING = OSCAL.parent / "itsg33-kubernetes-mapping.csv"
KUBE_NS = "https://oscal-compass.github.io/compliance-trestle/schemas/oscal/cd/kubernetes"


def write(tmp, name, text):
    p = Path(tmp) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


class LoadRules(unittest.TestCase):
    def test_missing_policy_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = write(tmp, "rules.csv", "rule_id,rule_description,control_ids,evidence_note\nghost,x,ac-6,\n")
            with self.assertRaisesRegex(ValueError, "ghost: no policy file"):
                bcd.load_rules(rules, Path(tmp) / "policies")

    def test_policy_name_must_match_rule_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = write(tmp, "rules.csv", "rule_id,rule_description,control_ids,evidence_note\nalpha,x,ac-6,\n")
            write(tmp, "policies/alpha/alpha.yaml", "apiVersion: kyverno.io/v1\nkind: ClusterPolicy\nmetadata:\n  name: beta\n")
            with self.assertRaisesRegex(ValueError, "alpha: .* metadata.name is beta"):
                bcd.load_rules(rules, Path(tmp) / "policies")

    def test_rule_for_an_unclaimed_control_is_an_error(self):
        rules = [{"id": "r", "description": "d", "controls": ["sc-13"], "note": ""}]
        with self.assertRaisesRegex(ValueError, "r: sc-13 is not claimed"):
            bcd.check_rule_controls(rules, {"ac-6"})

    def test_apparmor_rule_states_what_it_does_not_check(self):
        # Upstream checks only the beta annotation; the GA securityContext.appArmorProfile
        # field passes unchecked, so CM-6 evidence must say so.
        rule = next(r for r in bcd.load_rules(RULES, POLICIES) if r["id"] == "restrict-apparmor-profiles")
        self.assertIn("appArmorProfile", rule["note"])

    def test_repository_rules_load(self):
        rules = bcd.load_rules(RULES, POLICIES)
        self.assertEqual(len(rules), 24)
        self.assertEqual({c for r in rules for c in r["controls"]},
                         {"cm-6", "cm-7", "ac-6", "ia-5", "ac-17.400", "sc-5", "sc-2", "cm-2"})


class Build(unittest.TestCase):
    def setUp(self):
        with open(MAPPING) as f:
            rows = list(csv.DictReader(f))
        self.doc = bcd.build(rows, bcd.load_rules(RULES, POLICIES))["component-definition"]
        self.kube = next(c for c in self.doc["components"] if c["title"] == "Upstream Kubernetes")

    def test_kubernetes_component_carries_one_rule_set_per_rule(self):
        ids = [p["value"] for p in self.kube["props"] if p["name"] == "Rule_Id"]
        self.assertEqual(len(ids), 24)
        self.assertTrue(all(p["ns"] == KUBE_NS and p["remarks"].startswith("rule_set_") for p in self.kube["props"]))

    def test_covered_requirements_carry_rule_statements(self):
        reqs = {r["control-id"]: r for r in self.kube["control-implementations"][0]["implemented-requirements"]}
        smt = reqs["ac-6"]["statements"][0]
        self.assertEqual(smt["statement-id"], "ac-6_smt")
        self.assertEqual({p["value"] for p in smt["props"]},
                         {"restrict-wildcard-verbs", "restrict-binding-system-groups", "restrict-automount-sa-token"})
        self.assertNotIn("statements", reqs["sc-8"])

    def test_framework_short_name(self):
        props = self.kube["control-implementations"][0]["props"]
        self.assertIn({"name": "Framework_Short_Name", "ns": KUBE_NS, "value": "itsp.10.033-01-medium"}, props)

    def test_kyverno_is_a_validation_component_without_control_claims(self):
        kyv = next(c for c in self.doc["components"] if c["title"] == "Kyverno")
        self.assertEqual(kyv["type"], "validation")
        self.assertNotIn("control-implementations", kyv)
        self.assertEqual(len([p for p in kyv["props"] if p["name"] == "Check_Id"]), 24)


if __name__ == "__main__":
    unittest.main()
