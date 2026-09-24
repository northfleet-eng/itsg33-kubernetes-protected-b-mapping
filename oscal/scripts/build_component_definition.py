#!/usr/bin/env python3
"""Build an OSCAL component definition from the repository's mapping CSV and rules.

Usage: build_component_definition.py <oscal-dir> <mapping.csv> <rules.csv>

Three components:

  Upstream Kubernetes       the Admin rows: a cluster administrator configures an
                            upstream primitive (RBAC, NetworkPolicy, audit policy)
  Containerized workload    the Workload rows: the application's share
  Kyverno                   a validation component: it checks the Kubernetes
                            component's configuration and implements nothing

External rows are deliberately absent. They are the controls upstream Kubernetes cannot
satisfy on its own, so the gap analysis is a set difference a script computes
(scripts/gap.py) rather than a column in a spreadsheet. A control with an Admin or
Workload row and also an External row is claimed with coverage "partial".

rules.csv (oscal/policy/src/) names the Kyverno policy, and so the rule, that checks each
control offline. The rules are written in the OSCAL Compass convention that
compliance-to-policy reads: Rule_Id props on the implementing component, grouped by
remarks, and Rule_Id props on the statement of each covered implemented requirement.

This states what the components can do. It is not an assessment of any cluster.
"""
import csv
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

NS = "https://northfleetsecurity.ca/ns/oscal/cccs"
KUBE_NS = "https://oscal-compass.github.io/compliance-trestle/schemas/oscal/cd/kubernetes"
KYVERNO_NS = "https://oscal-compass.github.io/compliance-trestle/schemas/oscal/cd/kyverno"
FRAMEWORK = "itsp.10.033-01-medium"
UUID_NS = uuid.UUID("6b3f6f0e-2b8e-4d55-9a4b-6b1f0b2c4a10")
RELEASE = "2026-09-24"
SOURCE = "../profiles/itsp.10.033-01-medium/profile.json"
COMPONENTS = {
    "Admin": ("Upstream Kubernetes", "software",
              "Upstream Kubernetes (kube-apiserver, kubelet, etcd, and the built-in admission and "
              "authorization stack), configured by a cluster administrator. No distribution-specific "
              "or third-party component is assumed."),
    "Workload": ("Containerized workload", "software",
                 "The application running on the cluster. These requirements are the application "
                 "team's share of the control, distinct from the cluster's."),
}


def uid(*parts):
    return str(uuid.uuid5(UUID_NS, "/".join(parts)))


def oid(label):
    m = re.fullmatch(r"([A-Z]{2})-(\d+)(?:\((\d+)\))?", label.strip())
    return f"{m.group(1).lower()}-{int(m.group(2))}" + (f".{int(m.group(3))}" if m.group(3) else "")


def policy_name(text):
    """metadata.name of the first document in a Kyverno policy file."""
    in_meta = False
    for line in text.splitlines():
        if re.match(r"^\S", line):
            in_meta = line.startswith("metadata:")
        elif in_meta:
            m = re.match(r"^  name:\s*(\S+)\s*$", line)
            if m:
                return m.group(1).strip("'\"")
    return None


def load_rules(rules_csv, policies_dir):
    rules = []
    with open(rules_csv) as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        rid = row["rule_id"].strip()
        path = Path(policies_dir) / rid / f"{rid}.yaml"
        if not path.is_file():
            raise ValueError(f"{rid}: no policy file at {path}")
        name = policy_name(path.read_text())
        if name != rid:
            raise ValueError(f"{rid}: {path} metadata.name is {name}")
        rules.append({"id": rid, "description": row["rule_description"].strip(),
                      "controls": row["control_ids"].split(), "note": row["evidence_note"].strip()})
    return rules


def check_rule_controls(rules, claimed):
    for r in rules:
        for cid in r["controls"]:
            if cid not in claimed:
                raise ValueError(f"{r['id']}: {cid} is not claimed by the Upstream Kubernetes component")


def rule_props(rules, ns, kind):
    props = []
    for i, r in enumerate(rules):
        remarks = f"rule_set_{i:02d}"
        props.append({"name": "Rule_Id", "ns": ns, "value": r["id"], "remarks": remarks})
        if kind == "implementing":
            props.append({"name": "Rule_Description", "ns": ns, "value": r["description"], "remarks": remarks})
        else:
            props.append({"name": "Check_Id", "ns": ns, "value": r["id"], "remarks": remarks})
            props.append({"name": "Check_Description", "ns": ns, "value": r["description"], "remarks": remarks})
    return props


def build(rows, rules):
    external = {oid(r["Control"]) for r in rows if r["Category"] == "External"}
    admin = {oid(r["Control"]) for r in rows if r["Category"] == "Admin"}
    check_rule_controls(rules, admin)
    by_control = {}
    for r in rules:
        for cid in r["controls"]:
            by_control.setdefault(cid, []).append(r["id"])
    components = []
    for cat, (title, ctype, desc) in COMPONENTS.items():
        reqs = []
        for r in rows:
            if r["Category"] != cat:
                continue
            cid = oid(r["Control"])
            text = r["K8s Mechanism"].strip().rstrip(".") + "."
            if r["Notes"].strip():
                text += " " + r["Notes"].strip().rstrip(".") + "."
            req = {"uuid": uid("req", cat, cid), "control-id": cid, "description": text}
            if cid in external:
                req["props"] = [{"name": "coverage", "ns": NS, "value": "partial"}]
            if cat == "Admin" and cid in by_control:
                ids = by_control[cid]
                req["statements"] = [{
                    "statement-id": f"{cid}_smt",
                    "uuid": uid("stmt", cid),
                    "description": "Checked offline by the Kyverno rules " + ", ".join(ids) + ".",
                    "props": [{"name": "Rule_Id", "ns": KUBE_NS, "value": i} for i in ids],
                }]
            reqs.append(req)
        impl = {
            "uuid": uid("impl", title),
            "source": SOURCE,
            "description": f"{title} against the ITSP.10.033-01 Medium profile.",
            "implemented-requirements": reqs,
        }
        comp = {"uuid": uid("component", title), "type": ctype, "title": title, "description": desc}
        if cat == "Admin":
            impl["props"] = [{"name": "Framework_Short_Name", "ns": KUBE_NS, "value": FRAMEWORK}]
            comp["props"] = rule_props(rules, KUBE_NS, "implementing")
        comp["control-implementations"] = [impl]
        components.append(comp)
    components.append({
        "uuid": uid("component", "Kyverno"),
        "type": "validation",
        "title": "Kyverno",
        "description": "The Kyverno CLI, evaluating the rules offline against Kubernetes manifests. It checks "
                       "the Upstream Kubernetes component's configuration; it does not implement any control.",
        "props": rule_props(rules, KYVERNO_NS, "validation"),
    })
    doc = {
        "uuid": None,
        "metadata": {
            "title": "Upstream Kubernetes and containerized workloads: ITSP.10.033-01 Medium control implementation",
            "last-modified": RELEASE + "T00:00:00-04:00",
            "version": RELEASE.replace("-", "."),
            "oscal-version": "1.1.3",
            "roles": [{"id": "maintainer", "title": "Maintainer"}],
            "parties": [{"uuid": uid("party", "northfleet"), "type": "organization",
                         "name": "Northfleet Security Ltd.", "short-name": "Northfleet"}],
            "responsible-parties": [{"role-id": "maintainer", "party-uuids": [uid("party", "northfleet")]}],
            "remarks": "Generated from itsg33-kubernetes-mapping.csv and oscal/policy/src/rules.csv. Describes what "
                       "upstream Kubernetes and a workload can implement, and which Kyverno rules check it; it is not "
                       "an assessment of any system. Controls the mapping marks External are deliberately absent: "
                       "they are the gap.",
        },
        "components": components,
    }
    body = json.dumps(doc, ensure_ascii=False)
    doc["uuid"] = uid("component-definition", hashlib.sha256(body.encode()).hexdigest())
    return {"component-definition": {"uuid": doc["uuid"], **{k: v for k, v in doc.items() if k != "uuid"}}}


def main(oscal_dir, mapping_csv, rules_csv):
    root = Path(oscal_dir)
    with open(mapping_csv) as f:
        rows = list(csv.DictReader(f))
    try:
        rules = load_rules(rules_csv, root / "policy" / "kyverno" / "policies")
        doc = build(rows, rules)
    except ValueError as e:
        raise SystemExit(f"rules.csv: {e}")
    out = root / "component-definitions/upstream-kubernetes.json"
    with open(out, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
    comps = doc["component-definition"]["components"]
    n = sum(len(c["control-implementations"][0]["implemented-requirements"])
            for c in comps if "control-implementations" in c)
    print(f"{n} implemented requirements, {len(rules)} rules -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:4])
