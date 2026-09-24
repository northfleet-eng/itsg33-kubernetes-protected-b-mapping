#!/usr/bin/env python3
"""Normalize compliance-to-policy-go v1 assessment results into valid, deterministic OSCAL.

Usage: normalize_ar.py <assessment-results.json> <sample>   (rewrites the file in place)

C2P-Go v1 writes placeholders that are fine in a live cluster and invalid or unstable
here: random uuids, the current time, an import-ap href of "http://...", reviewed-controls
as an array where OSCAL requires one object, the method
"TEST-AUTOMATED" (OSCAL's values are EXAMINE, INTERVIEW, TEST, UNKNOWN), statement ids
where control ids belong, un-namespaced props, and, because manifests evaluated offline
have no Kubernetes UID, empty subject uuids; also a zero-value "expires" on every
observation and null values where OSCAL allows none. This step replaces each with a value
derived from the content, fixes every timestamp to the release date, drops the zero
expiry and every null, and records each evaluated Kubernetes object as an inventory item
in the result's local definitions, which its subjects reference.

OSCAL assessment results import an assessment plan, which imports a system security
plan, and oscal-cli loads that chain when it validates. import-ap points at the sample
plan build_plan.py writes to results/plan/, which sits at the same depth as each
results/<sample>/ so every relative link in the chain resolves from either place.
"""
import copy
import hashlib
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from normalize import canonical  # noqa: E402  (oscal/scripts/normalize.py)

NS = "https://northfleetsecurity.ca/ns/oscal/cccs"
UUID_NS = uuid.UUID("6b3f6f0e-2b8e-4d55-9a4b-6b1f0b2c4a10")
RELEASE = "2026-09-24"
STAMP = RELEASE + "T00:00:00-04:00"
KYVERNO_VERSION = "1.19.1"
C2P_VERSION = "1.0.0"


def uid(*parts):
    return str(uuid.uuid5(UUID_NS, "/".join(parts)))


def control_id(value):
    return value[:-4] if value.endswith("_smt") else value


def drop_nulls(x):
    if isinstance(x, dict):
        return {k: drop_nulls(v) for k, v in x.items() if v is not None}
    if isinstance(x, list):
        return [drop_nulls(v) for v in x if v is not None]
    return x


def rule_of(obs):
    return next(p["value"] for p in obs.get("props", []) if p["name"] == "assessment-rule-id")


def normalize(ar_root, sample):
    ar = drop_nulls(copy.deepcopy(ar_root["assessment-results"]))
    ar["metadata"] = {
        "title": f"Kyverno evaluation of the {sample} samples against the ITSP.10.033-01 rules",
        "last-modified": STAMP,
        "version": RELEASE.replace("-", "."),
        "oscal-version": "1.1.3",
        "remarks": f"Evidence about the sample manifests in oscal/policy/samples/{sample}, evaluated offline. "
                   "It is not an assessment of any system.",
    }
    ar["import-ap"] = {"href": "../plan/assessment-plan.json"}
    for res in ar.get("results", []):
        res["uuid"] = uid("result", sample)
        res["title"] = f"Kyverno CLI {KYVERNO_VERSION}, offline, {sample} samples"
        res["description"] = (f"Policies selected from the component definition by compliance-to-policy-go "
                              f"{C2P_VERSION} and evaluated with the Kyverno CLI {KYVERNO_VERSION} against "
                              f"oscal/policy/samples/{sample}.")
        res["start"] = STAMP
        res.pop("end", None)
        objects = {}
        reviewed = res.get("reviewed-controls", {})
        if isinstance(reviewed, list):  # C2P-Go v1 writes an array; OSCAL requires one object
            reviewed = {"control-selections": [s for r in reviewed for s in r.get("control-selections", [])]}
        res["reviewed-controls"] = reviewed
        for sel in reviewed.get("control-selections", []):
            fixed = []
            for inc in sel.get("include-controls", []):
                cid = inc["control-id"]
                entry = {"control-id": control_id(cid)}
                if cid != entry["control-id"]:
                    entry["statement-ids"] = [cid]
                fixed.append(entry)
            sel["include-controls"] = sorted(fixed, key=lambda e: e["control-id"])
        observations = []
        for obs in res.get("observations", []):
            rule = rule_of(obs)
            obs["uuid"] = uid("observation", sample, rule)
            obs["collected"] = STAMP
            obs["methods"] = ["TEST"]
            obs.pop("expires", None)
            for p in obs.get("props", []):
                p["ns"] = NS
                if p["name"] == "controls":
                    p["value"] = ",".join(control_id(v) for v in p["value"].split(",") if v)
            subjects = obs.get("subjects", [])
            for s in subjects:
                title = s.get("title", "")
                s["subject-uuid"] = objects.setdefault(title, uid("kubernetes-object", title))
                s["type"] = "inventory-item"
                for p in s.get("props", []):
                    p["ns"] = NS
            subjects.sort(key=lambda s: (s.get("title", ""), json.dumps(s.get("props", []), sort_keys=True)))
            if not subjects:
                obs.pop("subjects", None)
            observations.append(obs)
        res["observations"] = sorted(observations, key=rule_of)
        res.pop("local-definitions", None)
        if objects:
            res["local-definitions"] = {"inventory-items": [
                {"uuid": u, "description": t} for t, u in sorted(objects.items())]}
    ar.pop("back-matter", None)
    ar["uuid"] = "00000000-0000-0000-0000-000000000000"
    ar["uuid"] = uid("assessment-results", sample, hashlib.sha256(json.dumps(ar, sort_keys=True).encode()).hexdigest())
    return {"assessment-results": canonical(ar)}


def main(path, sample):
    doc = normalize(json.load(open(path)), sample)
    with open(path, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:3])
