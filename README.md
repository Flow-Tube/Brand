# Flow brand assets

Badges, banners and icon previews for the [Flow](https://github.com/Flow-Tube) projects, generated from config and served from one place:

```
https://assets.flow-tube.org/v1/...
```

| Folder | What |
| --- | --- |
| `v1/badges/pill/` | 60px download and call-to-action buttons |
| `v1/badges/split/` | 32px info chips (the shields.io replacement) |
| `v1/badges/tile/` | 152px project tiles for the org profile and website |
| `v1/banners/` | 1280×420 README banners, plus 1280×640 social previews (`-social-*.png`) |
| `v1/icons/` | Launcher icon previews (SVG and 512px PNG) |
| `v1/manifest.json` | Index of every asset |
| `tools/` | The generators and their config |

Every badge and banner has a `-light` and a `-dark` file; some also have `-animated` versions.
Text is outlined into paths, so nothing depends on fonts at view time.

## Regenerate locally

```sh
python3 -m venv .venv && . .venv/bin/activate
sh tools/setup.sh                         # pinned npm + pip deps, builds tools/fonts/gsf.ttf
python3 tools/flowbadges.py
python3 tools/flowbanners.py
python3 tools/flowicons.py --previews-only
python3 tools/make_manifest.py
python3 tools/check_assets.py --base origin/main
```

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
