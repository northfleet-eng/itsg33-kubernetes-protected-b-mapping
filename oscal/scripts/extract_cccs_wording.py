#!/usr/bin/env python3
"""Extract the CCCS wording of every control and enhancement in ITSP.10.033: the
statement as CCCS words it, the GC discussion, and whether CCCS marks it withdrawn.

Usage: extract_cccs_wording.py <itsp.10.033-e.pdf> <out.json>

The profile build attaches this text to the NIST-derived controls, so the resolved
catalogue reads in CCCS's words (Orders in Council, not executive orders; Canada, not
the Nation) while keeping NIST's parameter structure for tooling.

The PDF is the source of truth. This script is a transcription aid: its output is
committed to src/ and CI never runs it.
"""
import json
import re
import sys

from extract_canadian import (BASE_HEAD, SECTION, WRAP_GAP, join, oid, paragraphs, read_lines,
                              split_enhancements, split_sections, statement_items)


def flatten(lead, items, depth=0):
    out = [lead] if lead else []
    for it in items:
        out.append("  " * depth + f"{it['label']} {it['text']}")
        out += flatten("", it["children"], depth + 1)
    return out


def record(sections):
    sec = {}
    for name, lines in sections:
        sec.setdefault(name, []).extend(lines)
    rec = {}
    if "Withdrawn" in sec:
        rec["withdrawn"] = " ".join(l["t"] for l in sec["Withdrawn"])
    stmt = sec.get("Control", []) + sec.get("Activity", []) + sec.get("Statement", [])
    if stmt:
        rec["statement"] = "\n".join(flatten(*statement_items(stmt)))
    if "Control" in sec or "Activity" in sec:
        rec["type"] = "control" if "Control" in sec else "activity"
    gc = paragraphs(sec.get("GC discussion", []))
    if gc and gc != ["None."]:
        rec["gc_guidance"] = "\n\n".join(gc)
    return rec


def main(pdf_path, out_path):
    lines = read_lines(pdf_path)
    heads = []
    for i, ln in enumerate(lines):
        m = BASE_HEAD.match(ln["t"])
        if not m or ln["x0"] >= 40:
            continue
        j = i + 1
        while j < len(lines) and lines[j]["gap"] is not None and lines[j]["gap"] < WRAP_GAP \
                and not SECTION.match(lines[j]["t"]):
            j += 1
        s = SECTION.match(lines[j]["t"]) if j < len(lines) else None
        if s and s.group(1) in ("Control", "Activity", "Withdrawn"):
            heads.append((i, j))
    out = {}
    for n, (i, j) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        block = [l for l in lines[j:end] if not l["t"].startswith("Family:")]
        # Drop the family preamble paragraph that sits between the last control of one
        # family and the first of the next.
        fam_cut = next((k for k, l in enumerate(lines[j:end]) if l["t"].startswith("Family:")), None)
        if fam_cut is not None:
            block = lines[j:j + fam_cut]
        m = BASE_HEAD.match(lines[i]["t"])
        title = m.group(3)
        for l in lines[i + 1:j]:
            title = join(title, l["t"])
        cid = oid(m.group(1), m.group(2))
        sections = split_sections(block, max_x0=45)
        enh = [l for s, ls in sections if s == "Enhancements" for l in ls]
        rec = record([(s, ls) for s, ls in sections if s != "Enhancements"])
        rec["title"] = title
        out[cid] = rec
        for num, heading, body in split_enhancements(enh):
            erec = record(split_sections(body))
            erec["title"] = heading.split(": ", 1)[1] if ": " in heading else heading
            out[oid(m.group(1), m.group(2), num)] = erec
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print(f"{len(out)} controls and enhancements; "
          f"{sum(1 for r in out.values() if 'withdrawn' in r)} withdrawn; "
          f"{sum(1 for r in out.values() if 'gc_guidance' in r)} with GC discussion", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
