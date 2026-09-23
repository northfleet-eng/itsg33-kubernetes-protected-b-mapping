#!/usr/bin/env python3
"""Extract Table 4 of ITSP.10.033-01 (every control, activity and enhancement in the
catalogue, with the Medium profile's selection status) from the CCCS PDF into CSV.

Usage: extract_table4.py <itsp.10.033-01-e.pdf> <out.csv>

The PDF is the source of truth. This script is a transcription aid: its output is
committed to src/ and reviewed by hand, and CI never runs it.
"""
import csv
import re
import sys

import pdfplumber

HEADER = {"Control/", "Suggested for this", "Suggested placeholder",
          "Profile-specific notes", "Activity", "profile", "values"}
FIELDS = ["family", "number", "id", "name", "description", "type", "status",
          "placeholder_values", "profile_notes", "page"]


def oscal_id(family, number):
    m = re.fullmatch(r"(\d+)(?:\((\d+)\))?", number)
    base = f"{family.lower()}-{int(m.group(1))}"
    return base + (f".{int(m.group(2))}" if m.group(2) else "")


def main(pdf_path, out_path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            if pno < 16:
                continue
            for table in page.extract_tables():
                for cells in table:
                    if len(cells) != 8:
                        continue
                    c = [(x or "").strip() for x in cells]
                    if c[0] == "Family" or c[1] == "ID":
                        continue
                    if not c[0] and not c[1] and set(filter(None, c)) <= HEADER:
                        continue
                    if c[0] and c[1]:
                        rows.append({"family": c[0], "number": c[1], "name": c[2],
                                     "description": c[3], "type": c[4], "status": c[5],
                                     "placeholder_values": c[6], "profile_notes": c[7],
                                     "page": pno})
                    elif rows and not c[0] and not c[1]:
                        # A row that continues onto the next page.
                        prev = rows[-1]
                        for key, i in (("name", 2), ("description", 3), ("type", 4),
                                       ("status", 5), ("placeholder_values", 6),
                                       ("profile_notes", 7)):
                            if c[i]:
                                prev[key] = (prev[key] + "\n" + c[i]).strip()
    for r in rows:
        # The page footer number sometimes lands inside the last cell on a page.
        r["description"] = re.sub(r"\n(\d{1,3})$",
                                  lambda m: "" if abs(int(m.group(1)) - r["page"]) <= 1 else m.group(0),
                                  r["description"])
        r["id"] = oscal_id(r["family"], r["number"])
        for k in ("name", "type", "status"):
            r[k] = re.sub(r"\s*\n\s*", " ", r[k])
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows({k: r[k] for k in FIELDS} for r in rows)
    print(f"{len(rows)} rows", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
