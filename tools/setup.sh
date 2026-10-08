#!/usr/bin/env sh
# Installs the pinned generator dependencies and builds tools/fonts/gsf.ttf.
# Run from anywhere; everything lands next to this script.
#   npm: package-lock.json (fonts and icon sets)
#   pip: requirements.txt  (use a virtualenv, or set PIP_FLAGS)
set -e
cd "$(dirname "$0")"
npm ci --no-audit --no-fund
python3 -m pip install ${PIP_FLAGS:-} -r requirements.txt
mkdir -p fonts
python3 - <<'PY'
from fontTools.ttLib import TTFont
f = TTFont("node_modules/@fontsource-variable/google-sans-flex/files/google-sans-flex-latin-full-normal.woff2")
f.flavor = None
f.save("fonts/gsf.ttf")
PY
echo "Ready. Run: python3 flowbadges.py && python3 flowbanners.py && python3 flowicons.py --previews-only"
