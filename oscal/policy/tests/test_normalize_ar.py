"""Normalizing compliance-to-policy-go v1 output into valid, deterministic OSCAL."""
import copy
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from normalize_ar import NS, normalize  # noqa: E402

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[45][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def c2p_like():
    """The shape C2P-Go v1 emits, including its placeholders."""
    subject = lambda name, result: {"subject-uuid": "", "title": f"ApiVersion: v1, Kind: Pod, Namespace: d, Name: {name}",
                                    "type": "resource", "props": [{"name": "result", "value": result},
                                                                  {"name": "reason", "value": "r"}]}
    return {"assessment-results": {
        "uuid": "random", "metadata": {"title": "OSCAL Assessment Results", "last-modified": "2026-09-24T11:12:13Z",
                                       "version": "0.0.1", "oscal-version": "1.0.4"},
        "import-ap": {"href": "http://..."},
        "results": [{"uuid": "random", "title": "t", "description": "d", "start": "2026-09-24T11:12:13Z",
                     "local-definitions": {"inventory-items": None},
                     "reviewed-controls": [{"control-selections": [{"include-controls": [{"control-id": "ac-6_smt"}]}]}],
                     "observations": [
                         {"uuid": "random", "description": "Observation of rule zeta", "methods": ["TEST-AUTOMATED"],
                          "expires": "0001-01-01T00:00:00Z",
                          "props": [{"name": "assessment-rule-id", "value": "zeta"}, {"name": "controls", "value": "ac-6_smt"}],
                          "subjects": [subject("b", "fail"), subject("a", "pass")]},
                         {"uuid": "random", "description": "Observation of rule alpha", "methods": ["TEST-AUTOMATED"],
                          "props": [{"name": "assessment-rule-id", "value": "alpha"}, {"name": "controls", "value": "cm-6_smt"}],
                          "subjects": []}]}]}}


class Normalize(unittest.TestCase):
    def setUp(self):
        self.out = normalize(c2p_like(), "compliant")["assessment-results"]
        self.res = self.out["results"][0]

    def test_deterministic(self):
        self.assertEqual(normalize(c2p_like(), "compliant"), normalize(c2p_like(), "compliant"))

    def test_every_uuid_is_valid(self):
        self.assertRegex(self.out["uuid"], UUID)
        self.assertRegex(self.res["uuid"], UUID)
        for o in self.res["observations"]:
            self.assertRegex(o["uuid"], UUID)
            for s in o.get("subjects", []):
                self.assertRegex(s["subject-uuid"], UUID)

    def test_subjects_reference_inventory_items(self):
        items = {i["uuid"]: i["description"] for i in self.res["local-definitions"]["inventory-items"]}
        for o in self.res["observations"]:
            for s in o.get("subjects", []):
                self.assertEqual(s["type"], "inventory-item")
                self.assertEqual(items[s["subject-uuid"]], s["title"])

    def test_import_ap_points_at_the_sample_assessment_plan(self):
        self.assertEqual(self.out["import-ap"], {"href": "../plan/assessment-plan.json"})

    def test_no_nulls_and_no_zero_expiry(self):
        def walk(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    self.assertIsNotNone(v, k)
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(self.out)
        self.assertTrue(all("expires" not in o for o in self.res["observations"]))

    def test_metadata_and_timestamps_are_fixed(self):
        self.assertEqual(self.out["metadata"]["oscal-version"], "1.1.3")
        self.assertEqual(self.out["metadata"]["last-modified"], "2026-09-24T00:00:00-04:00")
        self.assertEqual(self.res["start"], "2026-09-24T00:00:00-04:00")
        self.assertTrue(all(o["collected"] == "2026-09-24T00:00:00-04:00" for o in self.res["observations"]))

    def test_methods_use_oscal_values(self):
        self.assertTrue(all(o["methods"] == ["TEST"] for o in self.res["observations"]))

    def test_c2p_props_get_a_namespace(self):
        for o in self.res["observations"]:
            self.assertTrue(all(p["ns"] == NS for p in o["props"]))
            for s in o.get("subjects", []):
                self.assertTrue(all(p["ns"] == NS for p in s["props"]))

    def test_reviewed_controls_array_becomes_one_object(self):
        # C2P-Go v1 writes an array; OSCAL requires a single object.
        self.assertIsInstance(self.res["reviewed-controls"], dict)

    def test_statement_ids_become_control_ids(self):
        sel = self.res["reviewed-controls"]["control-selections"][0]["include-controls"][0]
        self.assertEqual(sel, {"control-id": "ac-6", "statement-ids": ["ac-6_smt"]})
        zeta = next(o for o in self.res["observations"] if o["props"][0]["value"] == "zeta")
        self.assertIn({"name": "controls", "ns": NS, "value": "ac-6"}, zeta["props"])

    def test_empty_subjects_are_dropped_and_observations_sorted(self):
        rules = [next(p["value"] for p in o["props"] if p["name"] == "assessment-rule-id")
                 for o in self.res["observations"]]
        self.assertEqual(rules, ["alpha", "zeta"])
        self.assertNotIn("subjects", self.res["observations"][0])

    def test_input_is_not_mutated(self):
        src = c2p_like()
        before = copy.deepcopy(src)
        normalize(src, "compliant")
        self.assertEqual(src, before)


if __name__ == "__main__":
    unittest.main()
