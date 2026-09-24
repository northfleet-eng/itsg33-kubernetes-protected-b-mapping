"""The minimal assessment plan and system security plan the sample results import."""
import sys
import unittest
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(POLICY / "scripts"))
import build_plan  # noqa: E402

RULES = [{"id": "a", "controls": ["ac-6", "cm-6"]}, {"id": "b", "controls": ["ac-17.400", "ac-6"]}]


class BuildPlan(unittest.TestCase):
    def setUp(self):
        self.ssp, self.ap = build_plan.build(RULES)
        self.ssp_body = self.ssp["system-security-plan"]
        self.ap_body = self.ap["assessment-plan"]

    def test_plan_imports_the_ssp_beside_it(self):
        self.assertEqual(self.ap_body["import-ssp"], {"href": "../plan/ssp.json"})

    def test_ssp_imports_the_medium_profile_from_results_depth(self):
        href = self.ssp_body["import-profile"]["href"]
        self.assertEqual(href, "../../../profiles/itsp.10.033-01-medium/profile.json")
        self.assertTrue((POLICY / "results" / "plan" / href).resolve().is_file())

    def test_reviewed_controls_are_the_rule_controls(self):
        sel = self.ap_body["reviewed-controls"]["control-selections"][0]["include-controls"]
        self.assertEqual([c["control-id"] for c in sel], ["ac-6", "ac-17.400", "cm-6"])

    def test_each_control_is_implemented_by_the_sample_component(self):
        comp = self.ssp_body["system-implementation"]["components"][0]
        self.assertEqual(comp["type"], "this-system")
        reqs = self.ssp_body["control-implementation"]["implemented-requirements"]
        self.assertEqual([r["control-id"] for r in reqs], ["ac-6", "ac-17.400", "cm-6"])
        self.assertTrue(all(r["by-components"][0]["component-uuid"] == comp["uuid"] for r in reqs))
        self.assertIn("a, b", reqs[0]["by-components"][0]["description"])

    def test_says_it_is_not_a_real_system(self):
        self.assertIn("Not a real system", self.ssp_body["metadata"]["remarks"])
        self.assertIn("Not a real system", self.ap_body["metadata"]["remarks"])

    def test_deterministic(self):
        self.assertEqual(build_plan.build(RULES), build_plan.build(RULES))


if __name__ == "__main__":
    unittest.main()
