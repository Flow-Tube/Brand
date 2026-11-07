#!/usr/bin/env bash
set -euo pipefail

# Usage: fetch-stats.sh <out> [contributors.json]
# The contributor count comes from the contributors feed, so build that one first.
OUT="${1:?usage: fetch-stats.sh <out> [contributors.json]}"
CONTRIBUTORS_FILE="${2:-$(dirname "$OUT")/contributors.json}"
ANDROID_REPO="Flow-Tube/Flow"
DESKTOP_REPO="Flow-Tube/Flow-Desktop"
EXTENSION_REPO="Flow-Tube/Flow-Extension"

# Latest stable tag without the leading v. /releases/latest skips drafts and prereleases.
latest_version() {
  gh api "repos/$1/releases/latest" --jq '.tag_name | ltrimstr("v")'
}

android="$(gh api "repos/$ANDROID_REPO")"
desktop="$(gh api "repos/$DESKTOP_REPO")"
extension="$(gh api "repos/$EXTENSION_REPO")"
contributors="$(jq '.contributors | length' "$CONTRIBUTORS_FILE")"

downloads="$(gh api "repos/$ANDROID_REPO/releases" --paginate --jq '.[].assets[].download_count' | awk '{s+=$1} END {print s}')"
downloads="${downloads:-0}"

android_version="$(latest_version "$ANDROID_REPO")"
desktop_version="$(latest_version "$DESKTOP_REPO")"
extension_version="$(latest_version "$EXTENSION_REPO")"

jq -n \
  --argjson android "$android" \
  --argjson desktop "$desktop" \
  --argjson extension "$extension" \
  --argjson contributors "$contributors" \
  --argjson downloads "$downloads" \
  --arg androidVersion "$android_version" \
  --arg desktopVersion "$desktop_version" \
  --arg extensionVersion "$extension_version" \
  '{
    stars: $android.stargazers_count,
    forks: $android.forks_count,
    issues: $android.open_issues_count,
    watchers: $android.subscribers_count,
    contributors: $contributors,
    downloads: $downloads,
    versions: {
      android: $androidVersion,
      desktop: $desktopVersion,
      extension: $extensionVersion
    },
    repos: {
      android: { stars: $android.stargazers_count, forks: $android.forks_count },
      desktop: { stars: $desktop.stargazers_count, forks: $desktop.forks_count },
      extension: { stars: $extension.stargazers_count, forks: $extension.forks_count }
    }
  }' > "$OUT"
