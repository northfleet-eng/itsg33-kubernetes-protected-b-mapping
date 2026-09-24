#!/usr/bin/env bash
# Install the two pinned tools the policy pipeline needs into oscal/vendor/bin:
#   kyverno   Kyverno CLI v1.19.1 from the GitHub release, SHA-256 checked
#   c2pcli    OSCAL Compass compliance-to-policy-go v1.0.0, built from a git checkout
#             pinned to the tag's commit (the module cannot be fetched through the Go
#             module proxy: its test data has file names containing ':'); go.sum and
#             the Go checksum database verify the dependencies
# Idempotent: tools already at the pinned version are left alone.
set -euo pipefail
cd "$(dirname "$0")/../.."          # oscal/
BIN="$PWD/vendor/bin"
mkdir -p "$BIN"
KYVERNO_VERSION=v1.19.1
C2P_VERSION=v1.0.0
C2P_COMMIT=092a2590e949b46dac776bec59996ee374a996ae

os=$(uname -s | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)
case "$arch" in x86_64|amd64) arch=x86_64 ;; arm64|aarch64) arch=arm64 ;; esac
case "${os}_${arch}" in
  darwin_arm64)  sha=2cf5febbedaafca5d3c7819925a49f9723bf4c3337a1327b6f72970480af385a ;;
  darwin_x86_64) sha=d9d7a857755ccd027cba8b2a5146a515c1590d65b38cb37a2170809329e4f393 ;;
  linux_arm64)   sha=d78fecd183e1e6749c653fdb744c88d065e6737ec6856c97c4efac84bec54554 ;;
  linux_x86_64)  sha=b38228f367fc0fdc2b08f4c83ea50ac5f16c60ff8d62d76a66157c33c47b70ae ;;
  *) echo "unsupported platform: ${os}_${arch}" >&2; exit 1 ;;
esac

if ! "$BIN/kyverno" version 2>/dev/null | grep -q "${KYVERNO_VERSION#v}"; then
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/kyverno.tgz" \
    "https://github.com/kyverno/kyverno/releases/download/${KYVERNO_VERSION}/kyverno-cli_${KYVERNO_VERSION}_${os}_${arch}.tar.gz"
  if ! echo "$sha  $tmp/kyverno.tgz" | shasum -a 256 -c --status; then
    echo "Kyverno CLI archive does not match its pinned SHA-256" >&2
    exit 1
  fi
  tar -xzf "$tmp/kyverno.tgz" -C "$BIN" kyverno
  rm -rf "$tmp"
fi

if [ ! -x "$BIN/c2pcli" ]; then
  src=$(mktemp -d)
  git clone --quiet --depth 1 --branch "$C2P_VERSION" https://github.com/oscal-compass/compliance-to-policy-go.git "$src"
  got=$(git -C "$src" rev-parse HEAD)
  if [ "$got" != "$C2P_COMMIT" ]; then
    echo "compliance-to-policy-go $C2P_VERSION is $got, expected $C2P_COMMIT" >&2
    exit 1
  fi
  (cd "$src" && go build -o "$BIN/c2pcli" ./cmd/c2pcli)
  rm -rf "$src"
fi

echo "kyverno: $("$BIN/kyverno" version 2>&1 | grep -m1 -i version)"
echo "c2pcli:  $BIN/c2pcli (${C2P_VERSION})"
