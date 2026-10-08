# Contributing

## Assets come from config

Change assets through `tools/*.json` (and the generators in `tools/`), never by editing files in `v1/` by hand.
CI regenerates `v1/` on every change to `tools/`, so hand edits would be overwritten.

1. Edit `tools/badges.json`, `tools/banners.json` or `tools/palette.json`.
2. Open a PR. The `build` workflow renders everything, runs `tools/check_assets.py` and uploads `v1/` as an artifact.
3. Download the artifact and review the output.
4. Once merged, CI commits the regenerated `v1/` to `main` and Pages redeploys.

## The URL contract

Other repos and the website link straight to files under `v1/`. Once a file exists there it is never renamed, moved or deleted, and CI fails any change that does.
Add new files freely. A redesign that would change existing files goes into `v2/`.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org):

```
feat(badges): add F-Droid download pill
fix(banners): tighten tagline spacing on flow-desktop
chore(deps): bump simple-icons to 16.35.0
docs: explain the jsDelivr fallback
```

CI uses `chore(assets): regenerate` and `chore(stats): update release and download chips` for its own commits.
