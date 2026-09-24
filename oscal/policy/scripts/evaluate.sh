#!/usr/bin/env bash
# Evaluate the ITSP.10.033-01 rules against each sample set, offline, and write OSCAL
# assessment results and a Markdown summary per sample. See oscal/policy/README.md.
#
#   0. build_plan.py writes the minimal assessment plan and SSP the results import
#   1. c2pcli selects the Kyverno policies the component definition names  -> generated/
#   2. the Kyverno CLI evaluates them against samples/<sample>/              (no cluster)
#   3. report_adapter.py files the reports the way compliance-to-policy-go v1 reads them
#   4. c2pcli writes assessment results; normalize_ar.py makes them valid and stable
#   5. oscal-cli validates
#   6. summary.py writes results/<sample>/summary.md; check_verdicts.py fails on any
#      error verdict and compares with samples/expected.json
#
# Env: OSCAL_CLI (default oscal-cli), KYVERNO, C2PCLI (default oscal/vendor/bin/*),
#      SAMPLES (default "compliant noncompliant").
set -euo pipefail
cd "$(dirname "$0")/.."          # oscal/policy
BIN="$(cd .. && pwd)/vendor/bin"
KYVERNO="${KYVERNO:-$BIN/kyverno}"
C2P="${C2PCLI:-$BIN/c2pcli}"
CLI="${OSCAL_CLI:-oscal-cli}"
if [ ! -x "$KYVERNO" ] || [ ! -x "$C2P" ]; then scripts/install-tools.sh; fi
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fail() { [ -f "${2:-}" ] && cat "$2" >&2; echo "evaluate: $1" >&2; exit 1; }

python3 scripts/build_plan.py .
for doc in results/plan/ssp.json results/plan/assessment-plan.json; do
  "$CLI" validate "$doc" >"$tmp/validate.log" 2>&1 || { grep -v WARNING "$tmp/validate.log" >&2; fail "invalid: $doc"; }
done

rm -rf generated
mkdir -p "$tmp/o2p"      # c2pcli requires --temp-dir to exist
"$C2P" kyverno oscal2policy -c c2p-config.yaml --temp-dir "$tmp/o2p" -o generated >"$tmp/o2p.log" 2>&1 \
  || fail "c2pcli oscal2policy failed" "$tmp/o2p.log"
policies=()
while IFS= read -r f; do policies+=("$f"); done < <(find generated -name '*.yaml' | sort)
[ "${#policies[@]}" -gt 0 ] || fail "c2pcli selected no policies"

for sample in ${SAMPLES:-compliant noncompliant}; do
  python3 scripts/sample_guard.py "samples/$sample" || fail "samples/$sample is not rendered"
  out="$tmp/$sample.out"
  rc=0
  "$KYVERNO" apply "${policies[@]}" --resource "samples/$sample" --policy-report --output-format json \
    --remove-color >"$out" 2>&1 || rc=$?
  # 0: no violations; 1: violations found. Anything else is a Kyverno error.
  [ "$rc" -le 1 ] || fail "kyverno apply exited $rc on samples/$sample" "$out"
  python3 scripts/report_adapter.py "$out" "$tmp/$sample-results" || fail "no reports for $sample" "$out"
  mkdir -p "results/$sample" "$tmp/r2o-$sample"
  ar="results/$sample/assessment-results.json"
  "$C2P" kyverno result2oscal -c c2p-config.yaml --results "$tmp/$sample-results" --temp-dir "$tmp/r2o-$sample" \
    -o "$ar" >"$tmp/r2o.log" 2>&1 || fail "c2pcli result2oscal failed on $sample" "$tmp/r2o.log"
  python3 scripts/normalize_ar.py "$ar" "$sample"
  "$CLI" validate "$ar" >"$tmp/validate.log" 2>&1 || { grep -v WARNING "$tmp/validate.log" >&2; fail "invalid: $ar"; }
  python3 scripts/summary.py "$ar" src/rules.csv ../component-definitions/upstream-kubernetes.json "$sample" \
    > "results/$sample/summary.md"
  python3 scripts/check_verdicts.py samples/expected.json "$sample" "$ar"
  echo "evaluated $sample"
done
