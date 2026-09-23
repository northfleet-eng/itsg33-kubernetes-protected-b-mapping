#!/usr/bin/env python3
"""Transcribe the Canada-specific controls and enhancements of ITSP.10.033 from the
CCCS PDF into an OSCAL catalog.

Usage: extract_canadian.py <itsp.10.033-e.pdf> <table4.csv> <nist-catalog.json> <out.json>

"Canada-specific" is computed, not hand-listed: every identifier in the Table 4
extract that NIST SP 800-53 does not define, plus every control NIST withdrew that
CCCS kept active (SC-19). Each is parsed from the catalogue PDF: title, statement,
parameters, discussion, GC discussion, related controls, references, and withdrawal.

The PDF is the source of truth. This script is a transcription aid: its output is
committed to catalogs/ and reviewed by hand against the PDF, and CI never runs it.
"""
import csv
import hashlib
import json
import re
import sys
import uuid

import pdfplumber

NS = "https://northfleetsecurity.ca/ns/oscal/cccs"
UUID_NS = uuid.UUID("6b3f6f0e-2b8e-4d55-9a4b-6b1f0b2c4a10")  # this repository's uuid5 namespace
SECTION = re.compile(r"^(Control|Activity|Withdrawn|Discussion|GC discussion|"
                     r"Related controls and activities|Enhancements|References)\s*:\s*(.*)$")
BASE_HEAD = re.compile(r"^([A-Z]{2})-(\d{2,3}) (\S.*)$")
ENH_HEAD = re.compile(r"^\((\d{2,3})\)\s+(.+)$")
CTRL_REF = re.compile(r"\b([A-Z]{2})-(\d{2,3})(?:\((\d{2,3})\))?")
RELEASE = "2026-09-23"   # bump when the transcription changes
PARA_GAP = 7.0      # vertical gap (pt) that separates paragraphs in this PDF
WRAP_GAP = 4.0      # gap below which a line continues the previous one


def uid(*parts):
    return str(uuid.uuid5(UUID_NS, "/".join(parts)))


def oid(fam, num, enh=None):
    base = f"{fam.lower()}-{int(num)}"
    return base + (f".{int(enh)}" if enh is not None else "")


def padded(cid):
    """ac-17.400 -> AC-17(400) and ac-17.400 -> ac-17.400 zero-padded forms."""
    m = re.fullmatch(r"([a-z]{2})-(\d+)(?:\.(\d+))?", cid)
    fam, num, enh = m.group(1), int(m.group(2)), m.group(3)
    lab = f"{fam.upper()}-{num:02d}" + (f"({int(enh):02d})" if enh else "")
    sort = f"{fam}-{num:02d}" + (f".{int(enh):02d}" if enh else "")
    plain = f"{fam.upper()}-{num}" + (f"({int(enh)})" if enh else "")
    return lab, plain, sort


def ref_id(m):
    return oid(m.group(1), m.group(2), m.group(3))


# ---------------------------------------------------------------- PDF lines

def read_lines(pdf_path):
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, p in enumerate(pdf.pages, start=1):
            if pno < 29:
                continue
            for ln in p.extract_text_lines(layout=False, strip=True, return_chars=False):
                t = ln["text"]
                if ln["top"] < 40 and "UNCLASSIFIED" in t:
                    continue
                if ln["top"] > p.height - 60 and (re.fullmatch(r"\d+", t) or t == "ITSP.10.033"):
                    continue
                out.append({"p": pno, "top": ln["top"], "bottom": ln["bottom"], "x0": ln["x0"], "t": t})
    prev = None
    for ln in out:
        ln["gap"] = (ln["top"] - prev["bottom"]) if prev and prev["p"] == ln["p"] else None
        prev = ln
    return out


def join(a, b):
    if not a:
        return b
    if a.endswith("-") and not a.endswith(" -") and b[:1].isalnum():
        return a + b
    return a + " " + b


# ---------------------------------------------------------------- blocks

def find_base(lines, fam, num):
    head = re.compile(rf"^{fam}-{int(num):02d} \S")
    for i, ln in enumerate(lines):
        if head.match(ln["t"]) and ln["x0"] < 40:
            j = i + 1
            while j < len(lines) and lines[j]["gap"] is not None and lines[j]["gap"] < WRAP_GAP:
                j += 1
            if j < len(lines) and SECTION.match(lines[j]["t"]):
                return i
    raise KeyError(f"{fam}-{num} not found")


def base_block(lines, start):
    end = start + 1
    while end < len(lines):
        t = lines[end]["t"]
        if t.startswith("Family:"):
            break
        if BASE_HEAD.match(t) and lines[end]["x0"] < 40 and end + 1 < len(lines):
            j = end + 1
            while j < len(lines) and lines[j]["gap"] is not None and lines[j]["gap"] < WRAP_GAP:
                j += 1
            if j < len(lines) and SECTION.match(lines[j]["t"]) and SECTION.match(lines[j]["t"]).group(1) in (
                    "Control", "Activity", "Withdrawn"):
                break
        end += 1
    return lines[start:end]


def split_sections(block, max_x0=None):
    """Return [(section, [lines])...] for a base control (max_x0 set, so the Discussion
    and Related lines inside indented enhancements stay in the Enhancements section) or
    for an enhancement body (max_x0 None)."""
    sections, cur = [], None
    for ln in block:
        m = SECTION.match(ln["t"])
        if m and max_x0 is not None and ln["x0"] > max_x0:
            m = None
        if m:
            cur = (m.group(1), [])
            sections.append(cur)
            if m.group(2):
                cur[1].append(dict(ln, t=m.group(2)))
        elif cur is None:
            sections.append(("Statement", [ln]))
            cur = sections[-1]
        else:
            cur[1].append(ln)
    return sections


def split_enhancements(lines):
    """Split the Enhancements section into [(number, heading, body_lines)]."""
    out = []
    for ln in lines:
        m = ENH_HEAD.match(ln["t"])
        if m and ln["x0"] < 40:
            out.append([m.group(1), m.group(2), []])
        elif out:
            if not out[-1][2] and ln["x0"] < 40 and ln["gap"] is not None and ln["gap"] < WRAP_GAP:
                out[-1][1] = join(out[-1][1], ln["t"])       # wrapped heading
            else:
                out[-1][2].append(ln)
    return out


# ---------------------------------------------------------------- text

def paragraphs(lines):
    paras, cur = [], ""
    for ln in lines:
        t = ln["t"]
        bullet = t.startswith("•")
        if bullet:
            t = "- " + t.lstrip("• ").strip()
        new = cur == "" or bullet or (ln["gap"] is not None and ln["gap"] >= PARA_GAP)
        if new and cur:
            paras.append(cur)
            cur = ""
        cur = join(cur, t)
    if cur:
        paras.append(cur)
    # consecutive bullets form one markdown list
    merged = []
    for p in paras:
        if p.startswith("- ") and merged and merged[-1].split("\n")[-1].startswith("- "):
            merged[-1] += "\n" + p
        else:
            merged.append(p)
    return merged


def label_kind(lab):
    if lab.startswith("("):
        return "paren"
    if lab.isdigit():
        return "digit"
    if lab.isupper():
        return "upper"
    return "lower"


def statement_items(lines):
    """Parse statement lines into (lead_prose, tree of items). Items are dicts with
    label, text, children. Nesting follows label kind: the first kind seen is the top
    level, a new kind nests, a kind already on the stack pops back to it."""
    lead, roots, stack = "", [], []   # stack of (kind, item)
    cur = None
    for ln in lines:
        t = ln["t"]
        m = (re.match(r"^([A-Z]{1,2}|\d{1,2}|[a-z])\.\s+(.*)$", t)
             or re.match(r"^\(([a-z0-9]{1,3})\)\s+(.*)$", t)
             or re.match(r"^(\d{1,2})\)\s+(.*)$", t))
        if m:
            lab = m.group(1)
            if t.startswith("("):
                kind, label = "paren", f"({lab})"
            elif t[len(lab)] == ")":
                kind, label = "digit-paren", f"{lab})"
            else:
                kind, label = label_kind(lab), f"{lab}."
            item = {"label": label, "text": m.group(2), "children": []}
            kinds = [k for k, _ in stack]
            if kind in kinds:
                del stack[kinds.index(kind):]
            (stack[-1][1]["children"] if stack else roots).append(item)
            stack.append((kind, item))
            cur = item
        elif cur is None:
            lead = join(lead, t)
        else:
            cur["text"] = join(cur["text"], t)
    return lead, roots


# ---------------------------------------------------------------- params

class Params:
    def __init__(self, cid):
        lab, _, sort = padded(cid)
        self.prefix = sort   # ac-17.400 -> ac-17.400; pe-400.1 -> pe-400.01
        self.items = []

    def new(self, body):
        pid = f"{self.prefix}_odp.{len(self.items) + 1:02d}"
        p = {"id": pid}
        self.items.append(p)
        return p, pid

    def convert(self, text):
        out, i = "", 0
        while i < len(text):
            if text.startswith("[Assignment:", i) or text.startswith("[Selection", i):
                j, depth = i, 0
                while j < len(text):
                    if text[j] == "[":
                        depth += 1
                    elif text[j] == "]":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                inner = text[i + 1:j]
                out += "{{ insert: param, " + self.param(inner) + " }}"
                i = j + 1
            else:
                out += text[i]
                i += 1
        return out

    def param(self, inner):
        if inner.startswith("Assignment:"):
            p, pid = self.new(inner)
            p["label"] = inner[len("Assignment:"):].strip()
            return pid
        m = re.match(r"Selection\s*(?:\(([^)]*)\))?\s*:\s*(.*)$", inner, re.S)
        how, body = (m.group(1) or "").strip(), m.group(2)
        p, pid = self.new(inner)
        choices, depth, cur = [], 0, ""
        sep = ";" if self._top_level_has(body, ";") else ","
        for ch in body:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            if ch == sep and depth == 0:
                choices.append(cur.strip())
                cur = ""
            else:
                cur += ch
        if cur.strip():
            choices.append(cur.strip())
        p["select"] = {}
        if how.lower() in ("1 or more", "one or more"):
            p["select"]["how-many"] = "one-or-more"
        elif how.lower() in ("1", "one"):
            p["select"]["how-many"] = "one"
        p["select"]["choice"] = [self.convert(c) for c in choices]
        return pid

    @staticmethod
    def _top_level_has(body, sep):
        depth = 0
        for ch in body:
            depth += ch == "["
            depth -= ch == "]"
            if ch == sep and depth == 0:
                return True
        return False


# ---------------------------------------------------------------- controls

class Builder:
    def __init__(self):
        self.resources = {}   # title -> uuid

    def resource(self, title):
        title = re.sub(r"\s+", " ", title).strip().rstrip(".")
        if title not in self.resources:
            self.resources[title] = uid("reference", title)
        return self.resources[title]

    def control(self, cid, title, sections, cls, kind=None, parent=None):
        lab, plain, sort = padded(cid)
        ctl = {"id": cid, "class": cls, "title": title}
        props = [{"name": "label", "value": lab, "class": "zero-padded"},
                 {"name": "label", "value": plain},
                 {"name": "sort-id", "value": sort}]
        if kind:
            props.append({"name": "cccs-type", "ns": NS, "value": kind.lower()})
        if parent:
            props.append({"name": "cccs-parent-control", "ns": NS, "value": parent})
        links, parts = [], []
        params = Params(cid)
        sec = dict()
        for name, lines in sections:
            sec.setdefault(name, []).extend(lines)
        if "Withdrawn" in sec:
            text = " ".join(l["t"] for l in sec["Withdrawn"])
            props.append({"name": "status", "value": "withdrawn"})
            rel = "moved-to" if text.lower().startswith("moved") else "incorporated-into"
            for m in CTRL_REF.finditer(text):
                links.append({"href": f"#{ref_id(m)}", "rel": rel})
            parts.append({"id": f"{cid}_wdn", "name": "cccs-withdrawal", "ns": NS, "prose": text})
        stmt_lines = sec.get("Control", []) + sec.get("Activity", []) + sec.get("Statement", [])
        if stmt_lines:
            lead, items = statement_items(stmt_lines)
            smt = {"id": f"{cid}_smt", "name": "statement"}
            if lead:
                smt["prose"] = params.convert(lead)
            if items:
                smt["parts"] = [self.item(f"{cid}_smt", it, params) for it in items]
            parts.append(smt)
        for key, pname in (("Discussion", "guidance"), ("GC discussion", "gc-guidance")):
            paras = paragraphs(sec.get(key, []))
            if paras and paras != ["None."]:
                part = {"id": f"{cid}_{'gdn' if pname == 'guidance' else 'gcgdn'}", "name": pname,
                        "prose": "\n\n".join(paras)}
                if pname != "guidance":
                    part["ns"] = NS
                parts.append(part)
        rel_text = " ".join(l["t"] for l in sec.get("Related controls and activities", []))
        rel_text = re.sub(r"-\s+(\d)", r"-\1", rel_text)
        for m in CTRL_REF.finditer(rel_text):
            links.append({"href": f"#{ref_id(m)}", "rel": "related"})
        for para in paragraphs(sec.get("References", [])):
            for item in para.split("\n"):
                item = item[2:] if item.startswith("- ") else item
                # SC-401 opens its list with an instruction, not a reference.
                if item and item != "None." and not item.endswith(":"):
                    links.append({"href": f"#{self.resource(item)}", "rel": "reference"})
        if params.items:
            ctl["params"] = params.items
        ctl["props"] = props
        if links:
            ctl["links"] = links
        if parts:
            ctl["parts"] = parts
        return ctl

    def item(self, parent_id, it, params):
        suffix = it["label"].strip("().").lower()
        pid = f"{parent_id}.{suffix}"
        part = {"id": pid, "name": "item", "props": [{"name": "label", "value": it["label"]}],
                "prose": params.convert(it["text"])}
        if it["children"]:
            part["parts"] = [self.item(pid, c, params) for c in it["children"]]
        return part


def split_title(heading):
    """'Remote access: Privileged accounts remote access' -> 'Privileged accounts remote access'."""
    return heading.split(": ", 1)[1] if ": " in heading else heading


# ---------------------------------------------------------------- main

def main(pdf_path, table_csv, nist_path, out_path):
    table = {r["id"]: r for r in csv.DictReader(open(table_csv))}
    nist = {}

    def walk(cs):
        for c in cs:
            nist[c["id"]] = any(p["name"] == "status" and p["value"] == "withdrawn" for p in c.get("props", []))
            walk(c.get("controls", []))
    for g in json.load(open(nist_path))["catalog"]["groups"]:
        walk(g.get("controls", []))

    canadian = sorted(i for i in table if i not in nist)
    reinstated = sorted(i for i in table if nist.get(i) and table[i]["status"] != "NA"
                        and "Withdrawn:" not in table[i]["description"])
    lines = read_lines(pdf_path)
    fam_titles = {}
    # Family titles by the first control that follows each "Family:" line.
    cur = None
    for ln in lines:
        m = re.match(r"^Family: (.+)$", ln["t"])
        if m:
            cur = m.group(1).strip()
            continue
        mb = BASE_HEAD.match(ln["t"])
        if cur and mb:
            fam_titles.setdefault(mb.group(1).lower(), cur)
            cur = None

    b = Builder()
    groups = {}

    def group(fam):
        if fam not in groups:
            groups[fam] = {"id": fam, "class": "family", "title": fam_titles.get(fam, fam.upper()), "controls": []}
        return groups[fam]

    bases = sorted({re.sub(r"\..*$", "", i) for i in canadian if "." not in i or i.split(".")[0] not in nist}
                   | set(reinstated),
                   key=lambda x: (x.split("-")[0], int(x.split("-")[1].split(".")[0])))
    done = set()
    for base in bases:
        fam, num = base.split("-")
        start = find_base(lines, fam.upper(), num)
        block = base_block(lines, start)
        head = BASE_HEAD.match(block[0]["t"]).group(3)
        k = 1
        while k < len(block) and block[k]["gap"] is not None and block[k]["gap"] < WRAP_GAP and not SECTION.match(block[k]["t"]):
            head = join(head, block[k]["t"])
            k += 1
        sections = split_sections(block[k:], max_x0=45)
        enh_lines = [l for n, ls in sections if n == "Enhancements" for l in ls]
        sections = [(n, ls) for n, ls in sections if n != "Enhancements"]
        kind = next((n for n, _ in sections if n in ("Control", "Activity")), None)
        cls = "cccs-reinstated" if base in reinstated else "cccs-control"
        ctl = b.control(base, head, sections, cls, kind)
        subs = []
        for num_e, heading, body in split_enhancements(enh_lines):
            eid = f"{base}.{int(num_e)}"
            if eid not in table:
                raise KeyError(f"{eid} parsed from PDF but absent from Table 4")
            subs.append(b.control(eid, split_title(heading), split_sections(body),
                                  "cccs-enhancement", table[eid]["type"] if table[eid]["type"] != "NA" else None))
            done.add(eid)
        if subs:
            ctl["controls"] = subs
        group(fam)["controls"].append(ctl)
        done.add(base)

    # Canada-specific enhancements of NIST base controls.
    for eid in canadian:
        if eid in done:
            continue
        base, num_e = eid.split(".")
        fam, num = base.split("-")
        block = base_block(lines, find_base(lines, fam.upper(), num))
        sections = split_sections(block[1:], max_x0=45)
        enh_lines = [l for n, ls in sections if n == "Enhancements" for l in ls]
        found = [e for e in split_enhancements(enh_lines) if int(e[0]) == int(num_e)]
        if len(found) != 1:
            raise KeyError(f"{eid}: {len(found)} matches in PDF")
        _, heading, body = found[0]
        kind = table[eid]["type"] if table[eid]["type"] != "NA" else None
        group(fam)["controls"].append(
            b.control(eid, split_title(heading), split_sections(body), "cccs-enhancement", kind, parent=base))
        done.add(eid)

    missing = set(canadian) | set(reinstated)
    missing -= done
    if missing:
        raise SystemExit(f"not transcribed: {sorted(missing)}")

    order = [g for g in ["ac", "at", "au", "ca", "cm", "cp", "ia", "ir", "ma", "mp", "pe", "pl", "pm",
                         "ps", "pt", "ra", "sa", "sc", "si", "sr"] if g in groups]
    for g in groups.values():
        g["controls"].sort(key=lambda c: next(p["value"] for p in c["props"] if p["name"] == "sort-id"))

    pdf_sha = hashlib.sha256(open(pdf_path, "rb").read()).hexdigest()
    src_uuid = uid("source", "itsp.10.033-e.pdf", pdf_sha)
    resources = [{
        "uuid": src_uuid,
        "title": "Security and privacy controls and assurance activities catalogue (ITSP.10.033)",
        "props": [{"name": "type", "value": "standard"}],
        "citation": {"text": "Canadian Centre for Cyber Security, ITSP.10.033, March 31, 2026. "
                             "Contains information licensed under the Open Government Licence – Canada."},
        "rlinks": [{"href": "https://www.cyber.gc.ca/sites/default/files/itsp.10.033-e.pdf",
                    "media-type": "application/pdf",
                    "hashes": [{"algorithm": "SHA-256", "value": pdf_sha}]}],
    }] + [{"uuid": u, "title": t} for t, u in sorted(b.resources.items())]

    catalog = {
        "uuid": None,
        "metadata": {
            "title": "ITSP.10.033: Canada-specific controls and enhancements",
            "last-modified": RELEASE + "T00:00:00-04:00",
            "version": RELEASE.replace("-", "."),
            "oscal-version": "1.1.3",
            "props": [{"name": "marking", "value": "UNCLASSIFIED"}],
            "links": [{"href": f"#{src_uuid}", "rel": "source"}],
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
            "remarks": (
                "Unofficial transcription of the controls and enhancements that ITSP.10.033 defines and "
                "NIST SP 800-53 Rev. 5.2.0 does not: the 400-series controls and enhancements, and SC-19, "
                "which NIST withdrew and CCCS kept. Not reviewed or endorsed by CCCS; the PDF is "
                "authoritative. Contains information licensed under the Open Government Licence – Canada "
                "(https://open.canada.ca/en/open-government-licence-canada)."),
        },
        "groups": [groups[g] for g in order],
        "back-matter": {"resources": resources},
    }
    body = json.dumps(catalog, sort_keys=False, ensure_ascii=False)
    catalog["uuid"] = uid("catalog", hashlib.sha256(body.encode()).hexdigest())
    with open(out_path, "w") as f:
        json.dump({"catalog": catalog}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    n = sum(1 for _ in re.finditer(r'"class": "cccs-', json.dumps(catalog)))
    print(f"{n} Canada-specific controls and enhancements; reinstated: {reinstated}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
