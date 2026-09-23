#!/usr/bin/env bash
# Fetch the pinned inputs listed in src/sources.json and verify their SHA-256.
#   fetch.sh          NIST SP 800-53 catalog only (what the profiles import)
#   fetch.sh --pdfs   also the two CCCS PDFs, into vendor/, for re-running the extractors
# Exits non-zero if any file does not match its pin, which is also how a silent
# revision of a CCCS PDF shows up.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p vendor
fetch() {  # key dest
  local url sha
  url=$(python3 -c "import json,sys; print(json.load(open('src/sources.json'))[sys.argv[1]]['url'])" "$1")
  sha=$(python3 -c "import json,sys; print(json.load(open('src/sources.json'))[sys.argv[1]]['sha256'])" "$1")
  if [ ! -f "$2" ] || ! echo "$sha  $2" | shasum -a 256 -c --status; then
    curl -fsSL -A "Mozilla/5.0 (oscal-fetch)" -o "$2.part" "$url"
    mv "$2.part" "$2"
  fi
  if ! echo "$sha  $2" | shasum -a 256 -c --status; then
    echo "SHA-256 mismatch for $1 ($url)" >&2
    echo "  expected $sha" >&2
    echo "  got      $(shasum -a 256 "$2" | cut -d' ' -f1)" >&2
    exit 1
  fi
  echo "ok  $2"
}
fetch nist_catalog vendor/NIST_SP-800-53_rev5_catalog.json
if [ "${1:-}" = "--pdfs" ]; then
  fetch itsp.10.033 vendor/itsp.10.033-e.pdf
  fetch itsp.10.033-01 vendor/itsp.10.033-01-e.pdf
fi
