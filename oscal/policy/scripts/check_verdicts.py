#!/usr/bin/env python3
"""Compare a sample's rule verdicts with samples/expected.json, the test oracle.

Usage: check_verdicts.py <expected.json> <sample> <assessment-results.json>

Exits non-zero, listing every difference, if any rule's verdict is not the expected one,
if an expected rule is missing, or if a rule appears that expected.json does not list.
A sample expected.json has no entry for (your own manifests) is reported as not checked.
Any rule with an error verdict fails the check for every sample, listed or not.
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
    with open(expected_path) as f:
        oracle = json.load(f)
    with open(ar_path) as f:
        actual = rule_verdicts(json.load(f))
    errors = sorted(rule for rule, v in actual.items() if v["verdict"] == "error")
    if errors:
        # An error means Kyverno could not evaluate a rule; nothing about the sample is known.
        print(f"{sample}: rules errored: " + ", ".join(errors), file=sys.stderr)
        sys.exit(1)
    if sample not in oracle:
        # Someone's own manifests: there is nothing to check them against.
        print(f"{sample}: no entry in expected.json; verdicts not checked")
        return
    expected = oracle[sample]
    problems = compare(expected, actual)
    if problems:
        print(f"{sample}: verdicts differ from expected.json", *problems, sep="\n  ", file=sys.stderr)
        sys.exit(1)
    print(f"{sample}: {len(expected)} rules match expected.json")


if __name__ == "__main__":
    main(*sys.argv[1:4])
