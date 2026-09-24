#!/usr/bin/env python3
"""Turn Kyverno CLI report output into the four files compliance-to-policy-go v1 reads.

Usage: report_adapter.py <kyverno-output-file> <out-dir>

`kyverno apply --policy-report --output-format json` prints one JSON report per line,
interleaved with progress text. Kyverno 1.19 writes OpenReports (openreports.io/v1alpha1:
PolicyReport for namespaced resources, ClusterReport for cluster-scoped ones).
compliance-to-policy-go v1 reads wgpolicyk8s.io/v1beta1 PolicyReports, whose fields
OpenReports copied one for one, so the translation is an apiVersion and kind change.

C2P-Go v1 takes verdicts only from namespaced PolicyReports and ignores
ClusterPolicyReports, which would silently drop every cluster-scoped result (the
ClusterRoleBinding checks among them). This adapter files every report, cluster-scoped
ones included, as a PolicyReport, and writes the other three lists empty.

Output is JSON, which is valid YAML, sorted for determinism. Exits non-zero if the
Kyverno output held no reports at all, so an evaluation that never ran cannot pass.
"""
import json
import sys
from pathlib import Path

WG = "wgpolicyk8s.io/v1beta1"
REPORT_KINDS = ("PolicyReport", "ClusterReport", "ClusterPolicyReport")


def parse_cli_output(text):
    reports = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("kind") in REPORT_KINDS:
            reports.append(obj)
    return reports


def _result_key(r):
    res = r.get("resources", [{}])[0] if r.get("resources") else {}
    return (r.get("policy", ""), r.get("rule", ""), res.get("kind", ""), res.get("namespace", ""),
            res.get("name", ""), r.get("result", ""))


def to_c2p_lists(reports):
    items = []
    for rep in reports:
        meta = rep.get("metadata", {})
        ns = meta.get("namespace", "")
        items.append({
            "apiVersion": WG,
            "kind": "PolicyReport",
            "metadata": {"name": meta.get("name") or ("cluster-scoped" if not ns else ns), "namespace": ns},
            "results": sorted(rep.get("results", []), key=_result_key),
        })
    items.sort(key=lambda i: (i["metadata"]["namespace"], i["metadata"]["name"]))
    return {
        "policies.kyverno.io.yaml": {"apiVersion": "kyverno.io/v1", "kind": "PolicyList", "items": []},
        "clusterpolicies.kyverno.io.yaml": {"apiVersion": "kyverno.io/v1", "kind": "ClusterPolicyList", "items": []},
        "policyreports.wgpolicyk8s.io.yaml": {"apiVersion": WG, "kind": "PolicyReportList", "items": items},
        "clusterpolicyreports.wgpolicyk8s.io.yaml": {"apiVersion": WG, "kind": "ClusterPolicyReportList",
                                                     "items": []},
    }


def write(lists, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, doc in lists.items():
        (out / name).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")


def main(src, out_dir):
    reports = parse_cli_output(Path(src).read_text())
    if not reports:
        sys.exit(f"no policy reports in Kyverno output ({src})")
    write(to_c2p_lists(reports), out_dir)


if __name__ == "__main__":
    main(*sys.argv[1:3])
