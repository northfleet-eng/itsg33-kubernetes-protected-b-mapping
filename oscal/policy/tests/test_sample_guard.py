"""Unrendered Kustomize or Helm input is refused before evaluation."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(POLICY / "scripts"))
import sample_guard  # noqa: E402

DEPLOYMENT = "apiVersion: apps/v1\nkind: Deployment\nmetadata: {name: web, namespace: demo}\n"


def sample(files):
    tmp = tempfile.TemporaryDirectory()
    for name, text in files.items():
        p = Path(tmp.name) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return tmp


class Unrendered(unittest.TestCase):
    def test_rendered_samples_pass(self):
        self.assertEqual(sample_guard.unrendered(POLICY / "samples" / "compliant"), [])
        self.assertEqual(sample_guard.unrendered(POLICY / "samples" / "noncompliant"), [])

    def test_kustomization_file_is_refused(self):
        with sample({"base.yaml": DEPLOYMENT, "kustomization.yaml": "resources: [base.yaml]\n"}) as d:
            self.assertEqual(len(sample_guard.unrendered(d)), 1)

    def test_kustomization_kind_is_refused(self):
        doc = DEPLOYMENT + "---\napiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n"
        with sample({"all.yaml": doc}) as d:
            self.assertEqual(len(sample_guard.unrendered(d)), 1)

    def test_component_kind_is_refused(self):
        with sample({"c.yaml": "apiVersion: kustomize.config.k8s.io/v1alpha1\nkind: Component\n"}) as d:
            self.assertEqual(len(sample_guard.unrendered(d)), 1)

    def test_helm_chart_is_refused(self):
        with sample({"chart/Chart.yaml": "apiVersion: v2\nname: web\n", "chart/templates/d.yaml": DEPLOYMENT}) as d:
            self.assertEqual(len(sample_guard.unrendered(d)), 1)

    def test_cli_exits_non_zero_with_a_render_hint(self):
        with sample({"kustomization.yaml": "resources: []\n"}) as d:
            proc = subprocess.run([sys.executable, str(POLICY / "scripts" / "sample_guard.py"), d],
                                  capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("render", proc.stderr)


if __name__ == "__main__":
    unittest.main()
