#!/usr/bin/env python3
"""Compare two resolved catalogues by control identifier.

Usage: diff_resolved.py <a.json> <b.json>

Prints, as Markdown, the controls present in only one of the two and the controls whose
withdrawal status differs. Useful for checking a vendor's rendering of a profile against
this one, or one revision of this rendering against the next.
"""
import json
import sys


def controls(path):
    cat = json.load(open(path))["catalog"]
    out = {}

    def walk(cs):
        for c in cs:
            props = {p["name"]: p["value"] for p in c.get("props", [])}
            out[c["id"]] = {
                "title": props.get("cccs-title") or c.get("title", ""),
                "withdrawn": props.get("status") == "withdrawn" or props.get("cccs-status") == "withdrawn",
                "label": next((p["value"] for p in c.get("props", []) if p["name"] == "label" and "class" not in p),
                              c["id"].upper()),
            }
            walk(c.get("controls", []))
    for g in cat.get("groups", []):
        walk(g.get("controls", []))
    walk(cat.get("controls", []))
    return cat["metadata"].get("title", path), out


def key(cid):
    fam, rest = cid.split("-", 1)
    parts = [int(x) for x in rest.split(".")]
    return fam, parts


def main(a_path, b_path):
    a_title, a = controls(a_path)
    b_title, b = controls(b_path)
    only_a = sorted(set(a) - set(b), key=key)
    only_b = sorted(set(b) - set(a), key=key)
    status = sorted((i for i in set(a) & set(b) if a[i]["withdrawn"] != b[i]["withdrawn"]), key=key)
    out = [f"A: {a_title} ({len(a)} controls)  ", f"B: {b_title} ({len(b)} controls)", ""]
    for heading, ids, src in ((f"Only in A ({len(only_a)})", only_a, a), (f"Only in B ({len(only_b)})", only_b, b)):
        out += [f"## {heading}", ""]
        out += [f"- {src[i]['label']} {src[i]['title']}" + (" (withdrawn)" if src[i]["withdrawn"] else "")
                for i in ids] or ["None."]
        out.append("")
    out += [f"## Withdrawal status differs ({len(status)})", ""]
    out += [f"- {a[i]['label']}: A {'withdrawn' if a[i]['withdrawn'] else 'active'}, "
            f"B {'withdrawn' if b[i]['withdrawn'] else 'active'}" for i in status] or ["None."]
    print("\n".join(out))


if __name__ == "__main__":
    main(*sys.argv[1:3])
