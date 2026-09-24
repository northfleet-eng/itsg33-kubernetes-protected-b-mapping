"""Rule verdicts from an assessment-results document produced by this pipeline.

A rule's verdict is computed from the results of every resource it evaluated:
  error   any resource errored (the build fails on this)
  fail    any resource failed or warned
  pass    at least one resource was evaluated and all passed
  none    nothing was evaluated (no resource matched, or every result was skip)
"none" is never reported as a pass.

A control's verdict rolls up its rules' verdicts: satisfied only if every rule passed,
not satisfied if any failed, not evaluated if a rule evaluated nothing, error if any
rule errored.
"""
import re

EVALUATED = ("pass", "fail", "warn", "error")


def prop(obj, name, default=""):
    return next((p["value"] for p in obj.get("props", []) if p["name"] == name), default)


def verdict_of(results):
    evaluated = [r for r in results if r in EVALUATED]
    if not evaluated:
        return "none"
    if "error" in evaluated:
        return "error"
    if "fail" in evaluated or "warn" in evaluated:
        return "fail"
    return "pass"


def control_verdict(verdicts):
    if "error" in verdicts:
        return "error"
    if "fail" in verdicts:
        return "not satisfied"
    if "none" in verdicts:
        return "not evaluated"
    return "satisfied"


def label(cid):
    """ac-17.400 -> AC-17(400)"""
    m = re.fullmatch(r"([a-z]{2})-(\d+)(?:\.(\d+))?", cid)
    return f"{m.group(1).upper()}-{int(m.group(2))}" + (f"({int(m.group(3))})" if m.group(3) else "")


def rule_verdicts(ar_root):
    out = {}
    for result in ar_root["assessment-results"].get("results", []):
        for obs in result.get("observations", []):
            subjects = [(s.get("title", ""), prop(s, "result"), prop(s, "reason")) for s in obs.get("subjects", [])]
            out[prop(obs, "assessment-rule-id")] = {"verdict": verdict_of([r for _, r, _ in subjects]),
                                                    "subjects": subjects}
    return out
