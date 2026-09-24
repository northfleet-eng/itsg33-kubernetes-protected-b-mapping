"""Rule verdicts from an assessment-results document produced by this pipeline.

A rule's verdict is computed from the results of every resource it evaluated:
  error   any resource errored (the build fails on this)
  fail    any resource failed or warned
  pass    at least one resource was evaluated and all passed
  none    nothing was evaluated (no resource matched, or every result was skip)
"none" is never reported as a pass.
"""
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


def rule_verdicts(ar_root):
    out = {}
    for result in ar_root["assessment-results"].get("results", []):
        for obs in result.get("observations", []):
            subjects = [(s.get("title", ""), prop(s, "result"), prop(s, "reason")) for s in obs.get("subjects", [])]
            out[prop(obs, "assessment-rule-id")] = {"verdict": verdict_of([r for _, r, _ in subjects]),
                                                    "subjects": subjects}
    return out
