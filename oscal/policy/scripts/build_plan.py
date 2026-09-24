#!/usr/bin/env python3
"""Write the minimal assessment plan and system security plan the sample results import.

Usage: build_plan.py <policy-dir>   (writes <policy-dir>/results/plan/{ssp,assessment-plan}.json)

OSCAL assessment results import an assessment plan, which imports a system security
plan, which imports a profile; oscal-cli loads that chain when it validates results.
A sample evaluation has no real system, so these two documents describe the sample
manifests and nothing else, and say so. The plan reviews the controls the rules in
src/rules.csv evidence; the SSP implements each with one component, the samples.

results/plan/ sits at the same depth as results/<sample>/, because oscal-cli resolves
the links in an imported document against the importing results file's location; at
equal depth every relative link resolves the same from either place.
"""
import csv
import json
import re
import sys
import uuid
from pathlib import Path

UUID_NS = uuid.UUID("6b3f6f0e-2b8e-4d55-9a4b-6b1f0b2c4a10")
RELEASE = "2026-09-24"
STAMP = RELEASE + "T00:00:00-04:00"
NOT_REAL = ("Not a real system. OSCAL assessment results import an assessment plan, which imports a system "
            "security plan; this minimal pair exists so the sample evaluation's results form a valid chain. It "
            "describes the manifests in oscal/policy/samples/ and nothing else.")


def uid(*parts):
    return str(uuid.uuid5(UUID_NS, "/".join(parts)))


def sort_key(cid):
    m = re.fullmatch(r"([a-z]{2})-(\d+)(?:\.(\d+))?", cid)
    return m.group(1), int(m.group(2)), int(m.group(3) or 0)


def metadata(title):
    return {"title": title, "last-modified": STAMP, "version": RELEASE.replace("-", "."),
            "oscal-version": "1.1.3", "remarks": NOT_REAL}


def build(rules):
    by_control = {}
    for r in rules:
        for cid in r["controls"]:
            by_control.setdefault(cid, []).append(r["id"])
    controls = sorted(by_control, key=sort_key)
    component = uid("sample", "this-system")
    ssp = {"system-security-plan": {
        "uuid": uid("sample", "ssp"),
        "metadata": metadata("Sample evaluation target: ITSP.10.033-01 policy samples"),
        "import-profile": {"href": "../../../profiles/itsp.10.033-01-medium/profile.json"},
        "system-characteristics": {
            "system-ids": [{"identifier-type": "http://ietf.org/rfc/rfc4122", "id": uid("sample", "system")}],
            "system-name": "ITSP.10.033-01 policy samples",
            "description": "The Kubernetes manifests in oscal/policy/samples/, written to pass or to fail the rules. "
                           "Not a deployed system.",
            "system-information": {"information-types": [{
                "uuid": uid("sample", "information-type"),
                "title": "Sample Kubernetes manifests",
                "description": "Deployment, RBAC, and namespace manifests. No information is processed.",
            }]},
            "status": {"state": "other", "remarks": "Not a real system."},
            "authorization-boundary": {"description": "The files under oscal/policy/samples/."},
        },
        "system-implementation": {
            "users": [{"uuid": uid("sample", "user"), "title": "Evaluator",
                       "description": "Runs oscal/policy/scripts/evaluate.sh."}],
            "components": [{"uuid": component, "type": "this-system", "title": "Sample manifests",
                            "description": "The manifests the Kyverno CLI evaluates.",
                            "status": {"state": "other"}}],
        },
        "control-implementation": {
            "description": "Each requirement is checked offline by the Kyverno rules the component definition names.",
            "implemented-requirements": [{
                "uuid": uid("sample", "requirement", cid),
                "control-id": cid,
                "by-components": [{"component-uuid": component, "uuid": uid("sample", "by-component", cid),
                                   "description": "Checked by the Kyverno rules " + ", ".join(by_control[cid]) + "."}],
            } for cid in controls],
        },
    }}
    ap = {"assessment-plan": {
        "uuid": uid("sample", "assessment-plan"),
        "metadata": metadata("Sample evaluation plan: ITSP.10.033-01 policy samples"),
        "import-ssp": {"href": "../plan/ssp.json"},
        "reviewed-controls": {"control-selections": [{"include-controls": [{"control-id": c} for c in controls]}]},
    }}
    return ssp, ap


def main(policy_dir):
    root = Path(policy_dir)
    with open(root / "src" / "rules.csv") as f:
        rules = [{"id": r["rule_id"], "controls": r["control_ids"].split()} for r in csv.DictReader(f)]
    out = root / "results" / "plan"
    out.mkdir(parents=True, exist_ok=True)
    ssp, ap = build(rules)
    for name, doc in (("ssp.json", ssp), ("assessment-plan.json", ap)):
        with open(out / name, "w") as f:
            json.dump(doc, f, indent=1, ensure_ascii=False)
            f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
