#!/usr/bin/env bash
set -euo pipefail

# Usage: build.sh <outdir>   (needs GH_TOKEN, gh, jq and curl)
# Builds the /data/v1/ feeds. A file that fails validation is replaced by the live copy and
# marked "kept" in index.json. If the live copy can't be used either, the build fails and
# GitHub Pages keeps serving the last good deployment.
OUT="${1:?usage: build.sh <outdir>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIVE_URL="https://assets.flow-tube.org/data/v1"

mkdir -p "$OUT"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

valid() {
  local filter
  case "$1" in
    stats.json) filter='.stars > 0 and .downloads > 0' ;;
    changelogs.json) filter='type == "array" and any(.[]; .platform == "android")' ;;
    downloads.json) filter='.android != null and (.android.assets | length > 0)' ;;
    contributors.json) filter='.owner != null and (.contributors | length > 0)' ;;
  esac
  jq -e "$filter" "$2" > /dev/null 2>&1
}

# Contributors comes first: fetch-stats.sh reads the count from the file next to its own output.
statuses='{}'
for pair in contributors:fetch-contributors.sh stats:fetch-stats.sh changelogs:fetch-changelogs.sh downloads:fetch-downloads.sh; do
  file="${pair%%:*}.json"
  script="${pair#*:}"

  if bash "$HERE/$script" "$tmp/$file" && valid "$file" "$tmp/$file"; then
    status=fresh
  else
    echo "::warning::$file: fetch or validation failed, using the live copy"
    if ! curl -fsSL --retry 3 "$LIVE_URL/$file" -o "$tmp/$file" || ! valid "$file" "$tmp/$file"; then
      echo "::error::$file: no valid live copy at $LIVE_URL/$file"
      exit 1
    fi
    status=kept
  fi

  statuses="$(jq -c --arg file "$file" --arg status "$status" '. + {($file): $status}' <<<"$statuses")"
  echo "$file: $status"
done

run_url=""
if [ -n "${GITHUB_RUN_ID:-}" ]; then
  run_url="$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID"
fi

jq -n \
  --arg generatedAt "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg runUrl "$run_url" \
  --argjson files "$statuses" \
  '{
    generated_at: $generatedAt,
    run_url: (if $runUrl == "" then null else $runUrl end),
    files: $files
  }' > "$tmp/index.json"

mv "$tmp"/*.json "$OUT"/
