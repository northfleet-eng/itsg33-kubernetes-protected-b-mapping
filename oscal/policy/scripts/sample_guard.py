#!/usr/bin/env python3
"""Refuse a sample directory that still holds Kustomize or Helm sources.

Usage: sample_guard.py <sample-dir>

The Kyverno CLI evaluates the files it is given. Pointed at a Kustomize overlay it
evaluates the unpatched base and ignores the Kustomization, and pointed at a Helm chart
it evaluates whatever templates happen to parse, so either can pass over manifests that
will never be deployed. Exits non-zero, naming each file, if the directory contains a
kustomization file, a Kustomization or Component object, or a Helm Chart.yaml.
"""
import re
import sys
from pathlib import Path

KUSTOMIZE_FILES = {"kustomization.yaml", "kustomization.yml", "Kustomization"}
KUSTOMIZE_KIND = re.compile(r"^kind:\s*(Kustomization|Component)\s*$", re.M)


def unrendered(sample_dir):
    reasons = []
    for path in sorted(Path(sample_dir).rglob("*")):
        if not path.is_file():
            continue
        if path.name in KUSTOMIZE_FILES:
            reasons.append(f"{path}: Kustomize file")
        elif path.name == "Chart.yaml":
            reasons.append(f"{path}: Helm chart")
        elif path.suffix in (".yaml", ".yml") and KUSTOMIZE_KIND.search(path.read_text(errors="replace")):
            reasons.append(f"{path}: Kustomize object")
    return reasons


def main(sample_dir):
    reasons = unrendered(sample_dir)
    if reasons:
        print(f"{sample_dir} holds unrendered sources; render it first (kustomize build, helm template):",
              *reasons, sep="\n  ", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1])
