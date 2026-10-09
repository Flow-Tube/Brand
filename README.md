<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/banners/flow-tube-dark.svg">
  <img alt="Flow-Tube. Open-source, privacy-first YouTube and YouTube Music clients for every screen." src="https://assets.flow-tube.org/v1/banners/flow-tube-light.svg" width="100%">
</picture>

# Flow brand assets

Badges, banners and icon previews for the [Flow](https://github.com/Flow-Tube) projects, generated from config and served from one place:
**https://assets.flow-tube.org/v1/**. Browse them all, with copy-ready snippets, at **[assets.flow-tube.org](https://assets.flow-tube.org)**.

<p>
<a href="https://github.com/A-EDev/Flow/releases/latest"><picture><source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/pill/get-github-dark.svg"><img alt="Get it on GitHub" src="https://assets.flow-tube.org/v1/badges/pill/get-github-light.svg" height="60"></picture></a>
<a href="https://github.com/Flow-Tube/Flow-Desktop/releases/latest"><picture><source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/pill/get-linux-dark.svg"><img alt="Download for Linux" src="https://assets.flow-tube.org/v1/badges/pill/get-linux-light.svg" height="60"></picture></a>
<a href="https://patreon.com/A_EDev"><picture><source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/pill/support-patreon-dark.svg"><img alt="Support Flow on Patreon" src="https://assets.flow-tube.org/v1/badges/pill/support-patreon-light.svg" height="60"></picture></a>
</p>
<p>
<a href="https://github.com/A-EDev/Flow/releases/latest"><picture><source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/split/release-dark.svg"><img alt="Release" src="https://assets.flow-tube.org/v1/badges/split/release-light.svg" height="32"></picture></a>
<a href="https://github.com/A-EDev/Flow/releases"><picture><source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/split/downloads-dark.svg"><img alt="Downloads" src="https://assets.flow-tube.org/v1/badges/split/downloads-light.svg" height="32"></picture></a>
<a href="LICENSE"><picture><source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/split/license-dark.svg"><img alt="License: GPL-3.0" src="https://assets.flow-tube.org/v1/badges/split/license-light.svg" height="32"></picture></a>
</p>

| Folder | What | Size |
| --- | --- | --- |
| [`v1/badges/pill/`](v1/badges/pill) | Download and call-to-action buttons | 60px high |
| [`v1/badges/split/`](v1/badges/split) | Info chips, the shields.io replacement | 32px high |
| [`v1/badges/tile/`](v1/badges/tile) | Project tiles for the org profile and website | 152 × 152 |
| [`v1/banners/`](v1/banners) | README banners, plus social previews (`-social-*.png`) | 1280 × 420, 1280 × 640 |
| [`v1/icons/`](v1/icons) | Launcher icon previews, SVG and 512px PNG | 108dp canvas |
| [`v1/stars/`](v1/stars) | Star history charts, updated daily | 960 × 460 |
| [`v1/manifest.json`](v1/manifest.json) | Index of every file: kind, id, theme, size, alt text, link | |

Every badge and banner comes as `<id>-light.svg` and `<id>-dark.svg`, and some also as `<id>-light-animated.svg` / `<id>-dark-animated.svg`.
Text is outlined into paths, so the files look the same everywhere and need no fonts.

## The URL contract

**Files under `v1/` never change name, never move and are never deleted.** Their content can change (new numbers, small fixes), but every URL keeps working.
CI fails any change that removes or renames a `v1/` path. A redesign that can't keep that promise goes into `v2/`, next to `v1/`.

## Use the assets

Use `<picture>` with `prefers-color-scheme`, so readers with a dark theme get the dark file. GitHub supports this in READMEs.

**Pill** (60px):

```html
<a href="https://github.com/A-EDev/Flow/releases/latest">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/pill/get-github-dark.svg">
    <img alt="Get it on GitHub" src="https://assets.flow-tube.org/v1/badges/pill/get-github-light.svg" height="60">
  </picture>
</a>
```

**Info chip** (32px):

```html
<a href="https://github.com/A-EDev/Flow/releases/latest">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/split/release-dark.svg">
    <img alt="Release" src="https://assets.flow-tube.org/v1/badges/split/release-light.svg" height="32">
  </picture>
</a>
```

**Tile** (152px):

```html
<a href="https://github.com/A-EDev/Flow">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/badges/tile/tile-android-dark.svg">
    <img alt="Flow for Android" src="https://assets.flow-tube.org/v1/badges/tile/tile-android-light.svg" width="152">
  </picture>
</a>
```

**Banner** (full width):

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/banners/flow-android-dark.svg">
  <img alt="Flow. Privacy-first YouTube and YouTube Music for Android." src="https://assets.flow-tube.org/v1/banners/flow-android-light.svg" width="100%">
</picture>
```

**Star history chart** (full width, links to the stargazers):

```html
<a href="https://github.com/A-EDev/Flow/stargazers">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://assets.flow-tube.org/v1/stars/stars-flow-android-dark.svg">
    <img alt="Star history of Flow for Android" src="https://assets.flow-tube.org/v1/stars/stars-flow-android-light.svg" width="100%">
  </picture>
</a>
```

**Icon preview** (no light/dark versions):

```html
<img alt="Flow launcher icon: Scallop" src="https://assets.flow-tube.org/v1/icons/expressive_scallop-512.png" width="96" height="96">
```

The animated files rotate the shape slowly and stand still for readers who turn on reduced motion. Use them for one hero badge at most.

### React (website)

```jsx
const ASSETS = "https://assets.flow-tube.org/v1";

// kind: "pill" | "split" | "tile"; height in px (60, 32 or 152)
export function FlowBadge({ kind = "pill", id, alt, href, height = 60, theme }) {
  const file = (t) => `${ASSETS}/badges/${kind}/${id}-${t}.svg`;
  // With a site theme toggle, pass theme="light" | "dark"; otherwise follow the OS.
  const img = theme ? (
    <img src={file(theme)} alt={alt} height={height} />
  ) : (
    <picture>
      <source media="(prefers-color-scheme: dark)" srcSet={file("dark")} />
      <img src={file("light")} alt={alt} height={height} />
    </picture>
  );
  return href ? <a href={href}>{img}</a> : img;
}

// <FlowBadge id="get-github" alt="Get it on GitHub" href="https://github.com/A-EDev/Flow/releases/latest" />
```

`v1/manifest.json` lists every file with its `alt` text and `href`, if you'd rather build the list from data.

### Fallback: jsDelivr

If `assets.flow-tube.org` is ever unreachable, the same files are on jsDelivr, pinned to a tag:

```
https://cdn.jsdelivr.net/gh/Flow-Tube/Brand@v1.0.0/v1/badges/pill/get-github-light.svg
```

A tag is a snapshot, so the live numbers on the release and download chips stay at the tagged values.
READMEs should use `assets.flow-tube.org`; keep jsDelivr for the website's fallback.

## Add or change a badge

1. Edit [`tools/badges.json`](tools/badges.json) (or `banners.json`, `palette.json`).
   Icons are `si:<name>` from [Simple Icons](https://simpleicons.org), `ms:<name>` from [Material Symbols](https://fonts.google.com/icons) (Rounded, filled), or `flow` for the Flow mark.
   `category` picks the shape: `download`, `nightly`, `community`, `info`, `support`, `project`, `brand`.
2. Open a PR. The `build` workflow renders everything, runs [`tools/check_assets.py`](tools/check_assets.py) and uploads `v1/` as an artifact.
3. Download the artifact from the PR's checks and review the files.
4. Merge. CI commits the regenerated `v1/` to `main` (`chore(assets): regenerate`) and the site redeploys.

Never edit files in `v1/` by hand; CI would overwrite them. See [CONTRIBUTING.md](CONTRIBUTING.md).

### Run it locally

```sh
python3 -m venv .venv && . .venv/bin/activate
sh tools/setup.sh                          # pinned npm + pip deps, builds tools/fonts/gsf.ttf
python3 tools/flowbadges.py
python3 tools/flowbanners.py
python3 tools/flowicons.py --previews-only
python3 tools/make_manifest.py
python3 tools/check_assets.py --base origin/main
```

Dependencies are pinned in `tools/package-lock.json` and `tools/requirements.txt`, so CI renders the same bytes as your machine.
PNGs are rendered with [resvg](https://github.com/linebender/resvg), which needs no browser.

## Live numbers

The `release` and `downloads` chips (Flow for Android) and `desktop-release` and `desktop-downloads` (Flow Desktop) are refreshed by the [`stats`](.github/workflows/stats.yml) workflow:

- every day at 03:17 UTC, on demand, and when a `flow-release` event arrives (below)
- release = the newest stable tag, ignoring prereleases and drafts
- downloads = every asset of every release, rounded down so it never overstates: `950`, `9.1k+`, `48k+`, `1.2M+`
- the values are saved to `tools/badges.json` and only those chips are re-rendered; it commits only when an SVG changed

### Star history

The same `stats` run rebuilds the charts in `v1/stars/` with [`tools/flowstars.py`](tools/flowstars.py):

- Data comes from GitHub's `/repos/{owner}/{repo}/stargazers/history` endpoint: stars per day, no usernames, a page or two per repo. The built-in Actions token is enough.
- `tools/data/stars-state.json` keeps the last rendered totals. A chart whose totals haven't changed is skipped, so the "Updated" date doesn't create a commit every day. Run with `--force` to re-render anyway.
- To add a chart, add an entry to `charts` in [`tools/stars.json`](tools/stars.json) with an `id` (the file name), `href`, `title`, `subtitle`, `unit` and one or more `repos`. To add a repo to a chart, add `{"repo": "owner/name", "label": "...", "color": n}` to its `repos`.
- `color` picks the series colour: `0` is Flow red and `1` is Desktop blue. Give a project the same `color` in every chart, so it reads the same everywhere.
- Charts with one repo get milestone markers and a filled area; charts with several get a legend and labels at the line ends.
- Preview without touching the API: `python3 tools/flowstars.py --sample --out /tmp/stars`. Sample charts say "Sample data" and `check_assets.py` refuses them in `v1/`.

### Refresh right after a Flow release (optional)

Add this step to the end of the release workflow in `A-EDev/Flow`:

```yaml
      - name: Refresh the brand release chips
        env:
          GH_TOKEN: ${{ secrets.BRAND_DISPATCH_TOKEN }}
        run: gh api repos/Flow-Tube/Brand/dispatches -f event_type=flow-release
```

`BRAND_DISPATCH_TOKEN` is a fine-grained personal access token:

1. GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token.
2. Resource owner: **Flow-Tube**. Repository access: **Only select repositories** → `Flow-Tube/Brand`.
3. Repository permissions: **Contents: Read and write** (needed to send `repository_dispatch`). Metadata: Read-only is added automatically.
4. In `A-EDev/Flow` → Settings → Secrets and variables → Actions, add it as `BRAND_DISPATCH_TOKEN`.

The Flow-Tube org must allow fine-grained tokens (org Settings → Personal access tokens). The same step works from `Flow-Tube/Flow-Desktop`.

## Licensing

- Code in `tools/` and `site/`: [GPL-3.0](LICENSE), same as Flow.
- Generated artwork in `v1/`: [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt).
- Google Sans Flex, the typeface outlined into the artwork: [SIL OFL 1.1](LICENSES/OFL-1.1.txt).

## NOTICE

- GitHub, Reddit, Patreon, Weblate, Apple, Linux, Android and Obtainium names and logos are trademarks of their respective owners.
  Their use here identifies where to get Flow or how to reach the community and does not imply endorsement.
- The third-party logos come from [Simple Icons](https://simpleicons.org), released under CC0 1.0.
  (The Patreon badge uses a Material Symbols heart, not the Patreon logo.)
- Material Symbols are © Google, licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
- The Flow name and logo identify the Flow project. CC BY-SA 4.0 covers the artwork's copyright only, not trademark rights.
