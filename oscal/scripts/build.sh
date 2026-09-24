#!/usr/bin/env bash
# Rebuild everything derived from src/ and catalogs/: both profiles, both resolved
# catalogues, their CSV exports, the component definition, the gap report, and the
# policy evidence in policy/ (unit tests, then the offline Kyverno evaluation).
# Validates every OSCAL document with oscal-cli. Deterministic, so CI runs this and
# fails on any diff.
#
# Needs: python3, Java 17+, oscal-cli (on PATH, or OSCAL_CLI=/path/to/oscal-cli).
set -euo pipefail
cd "$(dirname "$0")/.."
CLI=${OSCAL_CLI:-oscal-cli}
NIST=vendor/NIST_SP-800-53_rev5_catalog.json
[ -f "$NIST" ] || scripts/fetch.sh

validate() {
  # oscal-cli reports dangling cross-references in a standalone catalog as warnings;
  # errors fail the build.
  local out
  if ! out=$("$CLI" validate "$1" 2>&1); then
    echo "$out" | grep -vE 'WARNING|Duplicate group' >&2
    echo "invalid: $1" >&2
    exit 1
  fi
  echo "valid  $1"
}

resolve() {  # profile out
  local out
  if ! out=$("$CLI" resolve-profile --to=json --overwrite "$1" "$2" 2>&1); then
    echo "$out" | grep -vE 'Duplicate group|should reference|The anchor at' >&2
    echo "resolution failed: $1" >&2
    exit 1
  fi
  python3 scripts/normalize.py "$1" "$2"
  echo "resolved $2"
}

python3 scripts/build_profiles.py . "$NIST"
validate catalogs/itsp.10.033-canadian-controls.json
validate profiles/itsp.10.033/profile.json
resolve profiles/itsp.10.033/profile.json resolved/itsp.10.033.json
validate resolved/itsp.10.033.json
validate profiles/itsp.10.033-01-medium/profile.json
resolve profiles/itsp.10.033-01-medium/profile.json resolved/itsp.10.033-01-medium.json
validate resolved/itsp.10.033-01-medium.json
python3 scripts/to_csv.py resolved/itsp.10.033.json resolved/itsp.10.033.csv
python3 scripts/to_csv.py resolved/itsp.10.033-01-medium.json resolved/itsp.10.033-01-medium.csv
python3 scripts/build_component_definition.py . ../itsg33-kubernetes-mapping.csv policy/src/rules.csv
validate component-definitions/upstream-kubernetes.json
python3 scripts/gap.py resolved/itsp.10.033-01-medium.json component-definitions/upstream-kubernetes.json \
  ../itsg33-kubernetes-mapping.csv > reports/gap-upstream-kubernetes.md
echo "wrote  reports/gap-upstream-kubernetes.md"
python3 -W error::ResourceWarning -m unittest discover -s policy/tests -q
OSCAL_CLI="$CLI" policy/scripts/evaluate.sh
