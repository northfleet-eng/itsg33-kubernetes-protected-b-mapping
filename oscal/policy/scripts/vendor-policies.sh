#!/usr/bin/env bash
# Copy every library policy named in kyverno/vendor.lock from upstream kyverno/policies,
# byte for byte, into kyverno/policies/<rule-id>/<rule-id>.yaml, plus upstream's LICENSE.
# Custom policies (source "custom") are left alone. Re-run after changing the lock.
set -euo pipefail
cd "$(dirname "$0")/.."          # oscal/policy
commit=""
while IFS=$'\t' read -r rule source; do
  case "$rule" in ''|'#'*) continue ;; esac
  [ "$source" = custom ] && continue
  commit=${source#kyverno/policies@}; commit=${commit%%:*}
  path=${source#*:}
  mkdir -p "kyverno/policies/$rule"
  curl -fsSL -o "kyverno/policies/$rule/$rule.yaml" \
    "https://raw.githubusercontent.com/kyverno/policies/$commit/$path"
  echo "vendored $rule"
done < kyverno/vendor.lock
curl -fsSL -o kyverno/LICENSE-kyverno-policies "https://raw.githubusercontent.com/kyverno/policies/$commit/LICENSE"
