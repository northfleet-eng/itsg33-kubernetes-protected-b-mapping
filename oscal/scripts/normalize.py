#!/usr/bin/env python3
"""Normalize a catalog resolved by oscal-cli from one of this repository's profiles.

Usage: normalize.py <profile.json> <resolved.json>   (rewrites resolved.json in place)

oscal-cli's as-is merge keeps each import's groups separate, so the resolved catalogue
has two "ac" groups, two "sa" groups, and so on. This step:

  1. folds each family's Canada-specific group into the NIST group of the same id;
  2. nests every Canada-specific enhancement of a NIST control (AC-17(400)) under its
     base control, in sort-id order;
  3. replaces the per-run uuid and timestamp with values derived from the content and
     the profile, and carries the profile's metadata (parties, roles, remarks) and
     source resources into the result.

Step 3 makes resolution reproducible, which is what lets CI fail on drift.
"""
import hashlib
import json
import os
import sys
import uuid

NS = "https://northfleetsecurity.ca/ns/oscal/cccs"
UUID_NS = uuid.UUID("6b3f6f0e-2b8e-4d55-9a4b-6b1f0b2c4a10")


# OSCAL's own model order for the keys that appear in catalogs; anything else sorts
# alphabetically after these. oscal-cli does not emit keys or back-matter resources in a
# stable order, so the output is canonicalized before hashing and writing.
KEY_ORDER = ["uuid", "metadata", "id", "class", "name", "ns", "value", "title", "published", "last-modified", "version",
             "oscal-version", "revisions", "document-ids", "label", "usage", "values", "select", "how-many",
             "choice", "guidelines", "constraints", "props", "links", "href", "rel", "media-type", "text",
             "citation", "rlinks", "hashes", "algorithm", "roles", "locations", "parties", "responsible-parties",
             "role-id", "party-uuids", "type", "short-name", "email-addresses", "params", "prose", "parts",
             "controls", "groups", "remarks", "back-matter", "resources"]
RANK = {k: i for i, k in enumerate(KEY_ORDER)}


def canonical(x):
    if isinstance(x, dict):
        return {k: canonical(x[k]) for k in sorted(x, key=lambda k: (RANK.get(k, len(RANK)), k))}
    if isinstance(x, list):
        return [canonical(v) for v in x]
    return x


def prop(ctl, name):
    return next((p["value"] for p in ctl.get("props", []) if p["name"] == name), None)


def sort_id(ctl):
    return prop(ctl, "sort-id") or ctl["id"]


def main(profile_path, resolved_path):
    profile_path = os.path.abspath(profile_path)
    profile = json.load(open(profile_path))["profile"]
    doc = json.load(open(resolved_path))
    cat = doc["catalog"]

    groups, order = {}, []
    for g in cat.get("groups", []):
        if g["id"] in groups:
            groups[g["id"]].setdefault("controls", []).extend(g.get("controls", []))
        else:
            groups[g["id"]] = g
            order.append(g["id"])
    for g in groups.values():
        top = {c["id"]: c for c in g.get("controls", [])}
        keep = []
        for c in g.get("controls", []):
            parent = prop(c, "cccs-parent-control")
            if parent and parent in top:
                top[parent].setdefault("controls", []).append(c)
            else:
                keep.append(c)
        for c in keep:
            if "controls" in c:
                c["controls"].sort(key=sort_id)
        g["controls"] = sorted(keep, key=sort_id)
    cat["groups"] = [groups[i] for i in order]

    pm = profile["metadata"]
    md = {
        "title": pm["title"],
        "last-modified": pm["last-modified"],
        "version": pm["version"],
        "oscal-version": pm["oscal-version"],
        "props": pm.get("props", []) + [{"name": "resolution-tool", "value": "libOSCAL-Java"}],
        "links": [{"href": os.path.relpath(profile_path, os.path.dirname(os.path.abspath(resolved_path))),
                   "rel": "source-profile"}] + pm.get("links", []),
        "roles": pm["roles"],
        "parties": pm["parties"],
        "responsible-parties": pm["responsible-parties"],
        "remarks": pm["remarks"],
    }
    cat["metadata"] = md
    resources = cat.setdefault("back-matter", {}).setdefault("resources", [])
    have = {r["uuid"] for r in resources}
    for r in profile.get("back-matter", {}).get("resources", []):
        if r["uuid"] not in have:
            resources.append(r)
    resources.sort(key=lambda r: (r.get("title", ""), r["uuid"]))
    cat["uuid"] = "00000000-0000-0000-0000-000000000000"
    body = json.dumps(cat, ensure_ascii=False, sort_keys=True)
    cat["uuid"] = str(uuid.uuid5(UUID_NS, "resolved/" + hashlib.sha256(body.encode()).hexdigest()))
    doc = {"catalog": canonical(cat)}
    with open(resolved_path, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:3])
