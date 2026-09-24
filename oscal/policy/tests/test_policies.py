"""Vendored and custom Kyverno policies: layout, provenance, and offline safety."""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1]
POLICIES = POLICY / "kyverno" / "policies"
LOCK = POLICY / "kyverno" / "vendor.lock"
KYVERNO = POLICY.parent / "vendor" / "bin" / "kyverno"


def lock_entries():
    for line in LOCK.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            rule, source = line.split("\t")
            yield rule, source


def policy_name(text):
    in_meta = False
    for line in text.splitlines():
        if re.match(r"^\S", line):
            in_meta = line.startswith("metadata:")
        elif in_meta:
            m = re.match(r"^  name:\s*(\S+)\s*$", line)
            if m:
                return m.group(1).strip("'\"")
    return None


class PolicyLayout(unittest.TestCase):
    def test_every_lock_entry_has_a_policy_named_for_its_directory(self):
        for rule, _ in lock_entries():
            path = POLICIES / rule / f"{rule}.yaml"
            self.assertTrue(path.is_file(), path)
            self.assertEqual(policy_name(path.read_text()), rule, path)

    def test_no_policy_directory_is_missing_from_the_lock(self):
        locked = {rule for rule, _ in lock_entries()}
        on_disk = {p.name for p in POLICIES.iterdir() if p.is_dir()}
        self.assertEqual(on_disk, locked)

    def test_lock_pins_one_upstream_commit(self):
        commits = {s.split("@")[1].split(":")[0] for _, s in lock_entries() if s != "custom"}
        self.assertEqual(commits, {"2716f4a26a3c27590a1d6d960dee4ce043e4fa4a"})

    def test_policies_run_offline(self):
        # A policy that looks things up in a live cluster or registry cannot run here.
        for rule, _ in lock_entries():
            text = (POLICIES / rule / f"{rule}.yaml").read_text()
            for marker in ("apiCall:", "imageRegistry:", "configMap:", "verifyImages:"):
                self.assertNotIn(marker, text, f"{rule} uses {marker}")


def kyverno_results(policy, resources_yaml):
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp) / "r.yaml"
        res.write_text(resources_yaml)
        out = subprocess.run([str(KYVERNO), "apply", str(policy), "--resource", str(res), "--policy-report",
                              "--output-format", "json", "--remove-color"], capture_output=True, text=True)
    results = {}
    for line in out.stdout.splitlines():
        if line.strip().startswith("{"):
            for r in json.loads(line).get("results", []):
                for s in r.get("resources", []):
                    results[s["name"]] = r["result"]
    return results


BINDINGS = """\
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata: {name: daw}
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: cluster-admin}
subjects: [{apiGroup: rbac.authorization.k8s.io, kind: Group, name: "itsp:daw-admins"}]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata: {name: sa-admin}
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: cluster-admin}
subjects: [{kind: ServiceAccount, name: legacy, namespace: default}]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata: {name: viewers}
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: view}
subjects: [{kind: ServiceAccount, name: legacy, namespace: default}]
"""


@unittest.skipUnless(KYVERNO.exists(), "run oscal/policy/scripts/install-tools.sh first")
class CustomPolicy(unittest.TestCase):
    def test_cluster_admin_only_to_the_daw_group(self):
        results = kyverno_results(POLICIES / "restrict-clusteradmin-subjects" / "restrict-clusteradmin-subjects.yaml",
                                  BINDINGS)
        self.assertEqual(results.get("daw"), "pass")
        self.assertEqual(results.get("sa-admin"), "fail")
        self.assertNotIn(results.get("viewers"), ("fail", "error"))

    def test_binding_without_subjects_is_not_an_error(self):
        binding = ("apiVersion: rbac.authorization.k8s.io/v1\nkind: ClusterRoleBinding\nmetadata: {name: empty}\n"
                   "roleRef: {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: cluster-admin}\n")
        results = kyverno_results(POLICIES / "restrict-clusteradmin-subjects" / "restrict-clusteradmin-subjects.yaml",
                                  binding)
        self.assertEqual(results.get("empty"), "pass")


if __name__ == "__main__":
    unittest.main()
