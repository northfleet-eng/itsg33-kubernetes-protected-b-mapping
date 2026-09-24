#!/usr/bin/env python3
"""Compare a sample's rule verdicts with samples/expected.json, the test oracle.

Usage: check_verdicts.py <expected.json> <sample> <assessment-results.json>

Exits non-zero, listing every difference, if any rule's verdict is not the expected one,
if an expected rule is missing, or if a rule appears that expected.json does not list.
"""
import json
import sys

from verdicts import rule_verdicts


def compare(expected, actual):
    problems = []
    for rule, want in sorted(expected.items()):
        got = actual.get(rule, {}).get("verdict", "missing")
        if got != want:
            problems.append(f"{rule}: expected {want}, got {got}")
    for rule in sorted(set(actual) - set(expected)):
        problems.append(f"{rule}: not in expected.json")
    return problems


def main(expected_path, sample, ar_path):
    expected = json.load(open(expected_path))[sample]
    problems = compare(expected, rule_verdicts(json.load(open(ar_path))))
    if problems:
        print(f"{sample}: verdicts differ from expected.json", *problems, sep="\n  ", file=sys.stderr)
        sys.exit(1)
    print(f"{sample}: {len(expected)} rules match expected.json")


if __name__ == "__main__":
    main(*sys.argv[1:4])
