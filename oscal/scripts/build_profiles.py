#!/usr/bin/env python3
"""Build the two OSCAL profiles from the committed sources in src/.

  profiles/itsp.10.033/profile.json
      The full ITSP.10.033 catalogue: NIST SP 800-53 Rev. 5.2.0 plus the Canada-specific
      catalog, with CCCS's own statement wording and GC discussion attached to every
      NIST-derived control.

  profiles/itsp.10.033-01-medium/profile.json
      The Medium profile (ITSP.10.033-01): the controls Table 4 marks Selected, the
      placeholder values it suggests, and its profile-specific notes.

Usage: build_profiles.py <oscal-dir> <nist-catalog.json>

Deterministic: identical inputs produce byte-identical output. CI rebuilds and fails
on any difference from what is committed.
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
NIST_HREF = "../../vendor/NIST_SP-800-53_rev5_catalog.json"
CANADIAN_HREF = "../../catalogs/itsp.10.033-canadian-controls.json"
OGL = ("Contains information licensed under the Open Government Licence – Canada "
       "(https://open.canada.ca/en/open-government-licence-canada).")

# Table 4 "Suggested placeholder values", bound to NIST SP 800-53 5.2.0 parameter ids.
# Values are the CCCS text with the brackets removed. Where CCCS gives one value per
# statement item and NIST has one parameter for all items, the value names the item.
# Where the 800-53 statement inserts an aggregate parameter (_prm_), the aggregate is
# set as well as the SP 800-53A parameters it stands for.
PARAMETER_VALUES = {
    "ac-1": {"ac-01_odp.05": ["at a frequency no longer than annually"],
             "ac-01_odp.07": ["at a frequency no longer than annually"]},
    "ac-2": {"ac-02_odp.10": ["at a frequency no longer than monthly"]},
    "ac-2.2": {"ac-02.02_odp.02": ["not to exceed 48 hours after no longer being required"]},
    "ac-2.3": {"ac-02.03_odp.01": ["not to exceed 30 days (items a. and b.)",
                                   "not to exceed 24 hours (item c.)"]},
    "ac-3.2": {"ac-03.02_odp": [
        "privileged commands: creation and deletion of PKI officers and administrators accounts",
        "actions: examples are: PKI changes to administrators and security officers; global "
        "administrator actions in cloud tenancies; domain administrator actions in single-forest systems"]},
    "ac-7": {"ac-07_odp.01": ["of a maximum of 5"],
             "ac-07_odp.02": ["period of at least 5 minutes"]},
    "ia-5.9": {"ia-05.09_odp": ["SSC"]},
    "ir-4.8": {"ir-04.08_odp.01": ["SSC", "TBS", "Cyber Centre"]},
    "mp-6.8": {"mp-06.08_odp.03": ["lost", "stolen", "upon termination of employment"]},
    "sa-10.7": {"sa-10.7_prm_1": ["SSC, TBS and Cyber Centre"],
                "sa-10.07_odp.01": ["SSC, TBS and Cyber Centre"],
                "sa-10.07_odp.02": ["SSC, TBS and Cyber Centre"],
                "sa-10.7_prm_2": ["SSC projects and services serving multiple departments"],
                "sa-10.07_odp.03": ["SSC projects and services serving multiple departments"],
                "sa-10.07_odp.04": ["SSC projects and services serving multiple departments"]},
    "sc-29": {"sc-29_odp": ["cyber security devices and tools"]},
    "si-3": {"si-03_odp.02": ["at least every 30 days"],
             "si-03_odp.04": ["quarantine malicious code"]},
    "si-7.1": {"si-7.1_prm_4": ["frequency at no longer than 30 days"],
               "si-07.01_odp.04": ["frequency at no longer than 30 days"],
               "si-07.01_odp.08": ["frequency at no longer than 30 days"],
               "si-07.01_odp.12": ["frequency at no longer than 30 days"]},
}


def uid(*parts):
    return str(uuid.uuid5(UUID_NS, "/".join(parts)))


def sort_key(cid):
    m = re.fullmatch(r"([a-z]{2})-(\d+)(?:\.(\d+))?", cid)
    return m.group(1), int(m.group(2)), int(m.group(3) or 0)


def metadata(title, remarks, sources):
    return {
        "title": title,
        "last-modified": RELEASE + "T00:00:00-04:00",
        "version": RELEASE.replace("-", "."),
        "oscal-version": "1.1.3",
        "props": [{"name": "marking", "value": "UNCLASSIFIED"}],
        "links": [{"href": f"#{u}", "rel": "source"} for u in sources],
        "roles": [{"id": "creator", "title": "Document Creator"},
                  {"id": "maintainer", "title": "Maintainer"}],
        "parties": [
            {"uuid": uid("party", "cccs"), "type": "organization",
             "name": "Canadian Centre for Cyber Security", "short-name": "CCCS"},
            {"uuid": uid("party", "northfleet"), "type": "organization",
             "name": "Northfleet Security Ltd.", "short-name": "Northfleet"}],
        "responsible-parties": [
            {"role-id": "creator", "party-uuids": [uid("party", "cccs")]},
            {"role-id": "maintainer", "party-uuids": [uid("party", "northfleet")]}],
        "remarks": remarks,
    }


def source(title, citation, href, sha):
    u = uid("source", href, sha)
    return u, {"uuid": u, "title": title, "props": [{"name": "type", "value": "standard"}],
               "citation": {"text": citation},
               "rlinks": [{"href": href, "media-type": "application/pdf",
                           "hashes": [{"algorithm": "SHA-256", "value": sha}]}]}


def finish(doc, key):
    body = json.dumps(doc, ensure_ascii=False)
    doc["uuid"] = uid(key, hashlib.sha256(body.encode()).hexdigest())
    ordered = {"uuid": doc["uuid"], **{k: v for k, v in doc.items() if k != "uuid"}}
    return {"profile": ordered}


def write(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def nist_index(path):
    idx = {}

    def walk(cs):
        for c in cs:
            idx[c["id"]] = {
                "withdrawn": any(p["name"] == "status" and p["value"] == "withdrawn" for p in c.get("props", [])),
                "title": c["title"],
                "params": {p["id"] for p in c.get("params", [])},
            }
            walk(c.get("controls", []))
    for g in json.load(open(path))["catalog"]["groups"]:
        walk(g.get("controls", []))
    return idx


def main(oscal_dir, nist_path):
    root = Path(oscal_dir)
    table = {r["id"]: r for r in csv.DictReader(open(root / "src/itsp.10.033-01-table4.csv"))}
    wording = json.load(open(root / "src/itsp.10.033-cccs-wording.json"))
    canadian_doc = json.load(open(root / "catalogs/itsp.10.033-canadian-controls.json"))["catalog"]
    canadian = set()

    def walk(cs):
        for c in cs:
            canadian.add(c["id"])
            walk(c.get("controls", []))
    for g in canadian_doc["groups"]:
        walk(g["controls"])
    nist = nist_index(nist_path)
    sources = json.load(open(root / "src/sources.json"))
    pdf_sha = sources["itsp.10.033"]["sha256"]

    # ------------------------------------------------------------ ITSP.10.033
    alters = []
    for cid in sorted(wording, key=sort_key):
        if cid in canadian or cid not in nist:
            continue
        w = wording[cid]
        if "withdrawn" in w and nist[cid]["withdrawn"]:
            continue
        adds_parts, adds_props = [], []
        kind = w.get("type") or (table[cid]["type"].lower() if cid in table and table[cid]["type"] != "NA" else None)
        if kind:
            adds_props.append({"name": "cccs-type", "ns": NS, "value": kind})
        if w["title"] != nist[cid]["title"]:
            adds_props.append({"name": "cccs-title", "ns": NS, "value": w["title"]})
        if "withdrawn" in w:
            adds_props.append({"name": "cccs-status", "ns": NS, "value": "withdrawn"})
            adds_parts.append({"id": f"{cid}_cccs_wdn", "name": "cccs-withdrawal", "ns": NS,
                               "prose": w["withdrawn"]})
        if "statement" in w:
            adds_parts.append({"id": f"{cid}_cccs_smt", "name": "cccs-statement", "ns": NS,
                               "prose": w["statement"]})
        if "gc_guidance" in w:
            adds_parts.append({"id": f"{cid}_gcgdn", "name": "gc-guidance", "ns": NS,
                               "prose": w["gc_guidance"]})
        add = {"position": "ending"}
        if adds_props:
            add["props"] = adds_props
        if adds_parts:
            add["parts"] = adds_parts
        alters.append({"control-id": cid, "adds": [add]})

    cat_src, cat_res = source(
        "Security and privacy controls and assurance activities catalogue (ITSP.10.033)",
        "Canadian Centre for Cyber Security, ITSP.10.033, effective March 31, 2026. " + OGL,
        "https://www.cyber.gc.ca/sites/default/files/itsp.10.033-e.pdf", pdf_sha)
    nist_src = uid("source", sources["nist_catalog"]["url"], sources["nist_catalog"]["sha256"])
    catalogue = {
        "uuid": None,
        "metadata": metadata(
            "ITSP.10.033: Security and privacy controls and assurance activities catalogue",
            "Unofficial OSCAL rendering of CCCS ITSP.10.033 (March 31, 2026). NIST SP 800-53 Rev. 5.2.0 "
            "supplies the control structure and parameters; the Canada-specific catalog supplies the "
            "controls NIST does not define. Every NIST-derived control carries CCCS's own statement "
            "wording (part cccs-statement) and GC discussion (part gc-guidance) as transcribed from the "
            "PDF; those parts, not the NIST statement, are the Canadian text. Not reviewed or endorsed "
            "by CCCS; the PDF is authoritative. " + OGL,
            [cat_src, nist_src]),
        "imports": [
            {"href": NIST_HREF, "include-all": {}, "exclude-controls": [{"with-ids": ["sc-19"]}]},
            {"href": CANADIAN_HREF, "include-all": {}},
        ],
        "merge": {"as-is": True},
        "modify": {"alters": alters},
        "back-matter": {"resources": [
            cat_res,
            {"uuid": nist_src, "title": "NIST SP 800-53 Rev. 5.2.0 catalog (OSCAL)",
             "props": [{"name": "type", "value": "standard"}],
             "rlinks": [{"href": sources["nist_catalog"]["url"], "media-type": "application/json",
                         "hashes": [{"algorithm": "SHA-256", "value": sources["nist_catalog"]["sha256"]}]}]},
        ]},
    }
    write(root / "profiles/itsp.10.033/profile.json", finish(catalogue, "profile-itsp.10.033"))

    # ------------------------------------------------------------ ITSP.10.033-01
    selected = sorted((i for i, r in table.items() if r["status"] == "Selected"), key=sort_key)
    for cid, values in PARAMETER_VALUES.items():
        assert cid in selected, cid
        for pid in values:
            assert pid in nist[cid]["params"], (cid, pid)
    set_params = [{"param-id": pid, "values": vals}
                  for cid in sorted(PARAMETER_VALUES, key=sort_key)
                  for pid, vals in PARAMETER_VALUES[cid].items()]
    note_alters = []
    for cid in selected:
        note = table[cid]["profile_notes"]
        if note and note != "NA":
            note_alters.append({"control-id": cid, "adds": [{"position": "ending", "parts": [
                {"id": f"{cid}_cccs_note", "name": "cccs-profile-note", "ns": NS,
                 "prose": re.sub(r"\s*\n\s*", " ", note)}]}]})
    prof_sha = sources["itsp.10.033-01"]["sha256"]
    prof_src, prof_res = source(
        "Suggested organizational security and privacy control and activity profile—Medium impact "
        "(ITSP.10.033-01)",
        "Canadian Centre for Cyber Security, ITSP.10.033-01, effective April 1, 2026. " + OGL,
        sources["itsp.10.033-01"]["url"], prof_sha)
    medium = {
        "uuid": None,
        "metadata": metadata(
            "ITSP.10.033-01: Suggested organizational security and privacy control and activity "
            "profile, Medium impact",
            f"Unofficial OSCAL rendering of CCCS ITSP.10.033-01 (April 1, 2026). Selects the {len(selected)} "
            "controls, activities and enhancements that Table 4 marks Selected, sets the placeholder values "
            "Table 4 suggests, and attaches its profile-specific notes. AC-2(10) is marked Selected in "
            "Table 4 although both CCCS documents list it as withdrawn (incorporated into AC-2); it is "
            "selected here as published and resolves as a withdrawn stub. Not reviewed or endorsed by "
            "CCCS; the PDF is authoritative. " + OGL,
            [prof_src]),
        "imports": [{"href": "../../resolved/itsp.10.033.json",
                     "include-controls": [{"with-ids": selected}]}],
        "merge": {"as-is": True},
        "modify": {"set-parameters": set_params, "alters": note_alters},
        "back-matter": {"resources": [prof_res]},
    }
    write(root / "profiles/itsp.10.033-01-medium/profile.json", finish(medium, "profile-itsp.10.033-01"))
    print(f"ITSP.10.033: {len(alters)} alters; ITSP.10.033-01: {len(selected)} selected, "
          f"{len(set_params)} parameter values, {len(note_alters)} notes", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
