#!/usr/bin/env python3
"""Flatten a resolved catalogue into one CSV row per control, activity and enhancement.

Usage: to_csv.py <resolved.json> <out.csv>

The statement column is CCCS's wording (the cccs-statement part for NIST-derived
controls, the transcribed statement for Canada-specific ones), not NIST's.
"""
import csv
import json
import re
import sys

FIELDS = ["id", "label", "family", "title", "source", "cccs_type", "status", "statement",
          "parameter_values", "gc_discussion", "profile_note"]
INSERT = re.compile(r"\{\{\s*insert:\s*param,\s*([^\s}]+)\s*\}\}")


def prop(c, name):
    return next((p["value"] for p in c.get("props", []) if p["name"] == name), None)


def part(c, name):
    return next((p for p in c.get("parts", []) if p["name"] == name), None)


def render(text, params):
    def sub(m):
        p = params.get(m.group(1), {})
        if p.get("values"):
            return "[" + "; ".join(p["values"]) + "]"
        if "select" in p:
            how = " (one or more)" if p["select"].get("how-many") == "one-or-more" else ""
            return f"[Selection{how}: " + "; ".join(render(ch, params) for ch in p["select"].get("choice", [])) + "]"
        return f"[Assignment: {p.get('label', m.group(1))}]"
    return INSERT.sub(sub, text or "")


def flat(p, params, depth=0):
    lab = prop(p, "label")
    out = []
    if p.get("prose"):
        out.append("  " * depth + (f"{lab} " if lab else "") + render(p["prose"], params))
    for sp in p.get("parts", []):
        out += flat(sp, params, depth + (1 if lab else 0))
    return out


def label(c):
    plain = [p["value"] for p in c.get("props", []) if p["name"] == "label" and "class" not in p]
    return plain[0] if plain else c["id"].upper()


def main(resolved, out):
    cat = json.load(open(resolved))["catalog"]
    rows = []

    def walk(controls, fam):
        for c in controls:
            params = {p["id"]: p for p in c.get("params", [])}
            withdrawn = prop(c, "status") == "withdrawn" or prop(c, "cccs-status") == "withdrawn"
            if part(c, "cccs-statement"):
                stmt = part(c, "cccs-statement")["prose"]
            elif part(c, "statement"):
                stmt = "\n".join(flat(part(c, "statement"), params))
            else:
                stmt = (part(c, "cccs-withdrawal") or {}).get("prose", "")
            values = "; ".join(f"{pid} = {' | '.join(p['values'])}" for pid, p in params.items() if p.get("values"))
            rows.append({
                "id": c["id"],
                "label": label(c),
                "family": fam,
                "title": prop(c, "cccs-title") or c["title"],
                "source": "CCCS" if c.get("class", "").startswith("cccs") else "NIST SP 800-53 Rev. 5.2.0",
                "cccs_type": prop(c, "cccs-type") or "",
                "status": "withdrawn" if withdrawn else "",
                "statement": stmt,
                "parameter_values": values,
                "gc_discussion": (part(c, "gc-guidance") or {}).get("prose", ""),
                "profile_note": (part(c, "cccs-profile-note") or {}).get("prose", ""),
            })
            walk(c.get("controls", []), fam)
    for g in cat.get("groups", []):
        walk(g.get("controls", []), g["id"].upper())
    walk(cat.get("controls", []), "")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
