#!/usr/bin/env python3
"""Build an OSCAL component definition from the repository's mapping CSV.

Usage: build_component_definition.py <oscal-dir> <mapping.csv>

Two components, one per implementation category that upstream software can claim:

  Upstream Kubernetes       the Admin rows: a cluster administrator configures an
                            upstream primitive (RBAC, NetworkPolicy, audit policy)
  Containerized workload    the Workload rows: the application's share

External rows are deliberately absent. They are the controls upstream Kubernetes cannot
satisfy on its own, so the gap analysis is a set difference a script computes
(scripts/gap.py) rather than a column in a spreadsheet. A control with an Admin or
Workload row and also an External row is claimed with coverage "partial".

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
UUID_NS = uuid.UUID("6b3f6f0e-2b8e-4d55-9a4b-6b1f0b2c4a10")
RELEASE = "2026-09-23"
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


def main(oscal_dir, mapping_csv):
    root = Path(oscal_dir)
    rows = list(csv.DictReader(open(mapping_csv)))
    external = {oid(r["Control"]) for r in rows if r["Category"] == "External"}
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
            reqs.append(req)
        components.append({
            "uuid": uid("component", title),
            "type": ctype,
            "title": title,
            "description": desc,
            "control-implementations": [{
                "uuid": uid("impl", title),
                "source": SOURCE,
                "description": f"{title} against the ITSP.10.033-01 Medium profile.",
                "implemented-requirements": reqs,
            }],
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
            "remarks": "Generated from itsg33-kubernetes-mapping.csv. Describes what upstream Kubernetes and a "
                       "workload can implement; it is not an assessment of any system. Controls the mapping marks "
                       "External are deliberately absent: they are the gap.",
        },
        "components": components,
    }
    body = json.dumps(doc, ensure_ascii=False)
    doc["uuid"] = uid("component-definition", hashlib.sha256(body.encode()).hexdigest())
    doc = {"uuid": doc["uuid"], **{k: v for k, v in doc.items() if k != "uuid"}}
    out = root / "component-definitions/upstream-kubernetes.json"
    with open(out, "w") as f:
        json.dump({"component-definition": doc}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    n = sum(len(c["control-implementations"][0]["implemented-requirements"]) for c in components)
    print(f"{n} implemented requirements -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
