"""Kyverno CLI report output in, the four list files C2P-Go v1 reads out."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(POLICY / "scripts"))
import report_adapter as ra  # noqa: E402

FIXTURES = POLICY / "tests" / "fixtures"
C2P = POLICY.parent / "vendor" / "bin" / "c2pcli"
WG = "wgpolicyk8s.io/v1beta1"

NOISE = """Applying 2 policy rules to 3 resources...
----------------------------------------------------------------------
{"apiVersion":"openreports.io/v1alpha1","kind":"PolicyReport","metadata":{"name":"ns","namespace":"demo"},"results":[{"policy":"p","rule":"r","result":"fail","resources":[{"kind":"Pod","name":"a","namespace":"demo"}]}]}
{"apiVersion":"openreports.io/v1alpha1","kind":"ClusterReport","metadata":{"name":"merged"},"results":[{"policy":"q","rule":"r","result":"fail","resources":[{"kind":"ClusterRoleBinding","name":"b"}]}]}
pass: 0, fail: 2, warn: 0, error: 0, skip: 0
"""


class Parse(unittest.TestCase):
    def test_reports_are_picked_out_of_progress_text(self):
        kinds = [r["kind"] for r in ra.parse_cli_output(NOISE)]
        self.assertEqual(kinds, ["PolicyReport", "ClusterReport"])

    def test_output_without_reports_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "out"
            src.write_text("Error: failed to load resources\n")
            proc = subprocess.run([sys.executable, str(POLICY / "scripts" / "report_adapter.py"), str(src),
                                   str(Path(tmp) / "res")], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("no policy reports in Kyverno output", proc.stderr)


class Translate(unittest.TestCase):
    def setUp(self):
        self.lists = ra.to_c2p_lists(ra.parse_cli_output(NOISE))

    def test_four_files(self):
        self.assertEqual(set(self.lists), {"policies.kyverno.io.yaml", "clusterpolicies.kyverno.io.yaml",
                                           "policyreports.wgpolicyk8s.io.yaml",
                                           "clusterpolicyreports.wgpolicyk8s.io.yaml"})

    def test_cluster_scoped_results_are_filed_where_c2p_reads(self):
        reports = self.lists["policyreports.wgpolicyk8s.io.yaml"]["items"]
        policies = sorted(r["policy"] for rep in reports for r in rep["results"])
        self.assertEqual(policies, ["p", "q"])
        self.assertEqual(self.lists["clusterpolicyreports.wgpolicyk8s.io.yaml"]["items"], [])

    def test_reports_use_the_wgpolicyk8s_api(self):
        for rep in self.lists["policyreports.wgpolicyk8s.io.yaml"]["items"]:
            self.assertEqual((rep["apiVersion"], rep["kind"]), (WG, "PolicyReport"))

    def test_fixture_from_the_real_cli(self):
        reports = ra.parse_cli_output((FIXTURES / "kyverno-apply.out").read_text())
        self.assertTrue(any(r["kind"] == "ClusterReport" for r in reports))


@unittest.skipUnless(C2P.exists(), "run oscal/policy/scripts/install-tools.sh first")
class C2PReadsTheAdaptedFiles(unittest.TestCase):
    def test_cluster_scoped_binding_reaches_the_assessment_results(self):
        spike = FIXTURES / "spike"
        with tempfile.TemporaryDirectory() as tmp:
            ra.write(ra.to_c2p_lists(ra.parse_cli_output((FIXTURES / "kyverno-apply.out").read_text())),
                     Path(tmp) / "results")
            out = Path(tmp) / "ar.json"
            (Path(tmp) / "t").mkdir()  # c2pcli requires --temp-dir to exist
            subprocess.run([str(C2P), "kyverno", "result2oscal", "-c", "c2p-config.yaml", "--results",
                            str(Path(tmp) / "results"), "--temp-dir", str(Path(tmp) / "t"), "-o", str(out)],
                           cwd=spike, check=True, capture_output=True)
            ar = json.loads(out.read_text())["assessment-results"]
        obs = {next(p["value"] for p in o["props"] if p["name"] == "assessment-rule-id"): o
               for o in ar["results"][0]["observations"]}
        results = [p["value"] for s in obs["restrict-binding-system-groups"].get("subjects", [])
                   for p in s["props"] if p["name"] == "result"]
        self.assertIn("fail", results)


if __name__ == "__main__":
    unittest.main()
