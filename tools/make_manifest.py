#!/usr/bin/env python3
"""Writes v1/manifest.json, an index of every published asset.

One entry per file: path, kind, id, theme, animated, format, width, height, alt, href, bytes.
The output has no timestamps, so it only changes when the assets do.

  python3 make_manifest.py           # write v1/manifest.json
"""
import json, os, re, struct
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.normpath(os.path.join(HERE, "..", "v1"))
MANIFEST = os.path.join(V1, "manifest.json")
BASE_URL = "https://assets.flow-tube.org/v1/"
KINDS = {"badges/pill": "pill", "badges/split": "split", "badges/tile": "tile", "banners": "banner", "icons": "icon",
         "stars": "stars"}
NAME = re.compile(r"^(?P<id>.+?)(?:-(?P<theme>light|dark))?(?P<animated>-animated)?(?:-(?P<px>\d+))?\.(?P<ext>svg|png)$")
SVG_NS = "{http://www.w3.org/2000/svg}"

def hrefs():
    cfg = json.load(open(os.path.join(HERE, "badges.json")))
    links = {b["id"]: b["href"] for items in cfg.values() for b in items if b.get("href")}
    stars = json.load(open(os.path.join(HERE, "stars.json")))
    links.update({c["id"]: c["href"] for c in stars["charts"] if c.get("href")})
    return links

def svg_info(path):
    root = ET.parse(path).getroot()
    title = root.find(SVG_NS + "title")
    num = lambda v: int(float(v)) if v is not None else None
    return num(root.get("width")), num(root.get("height")), title.text if title is not None else None

def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])

def asset_files():
    for folder in sorted(KINDS):
        d = os.path.join(V1, folder)
        for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if NAME.match(name):
                yield folder, name

def build():
    links = hrefs()
    assets = []
    for folder, name in asset_files():
        m = NAME.match(name)
        path = os.path.join(V1, folder, name)
        if m["ext"] == "svg":
            w, h, alt = svg_info(path)
        else:
            w, h = png_size(path)
            # a PNG is a raster of the SVG next to it (social previews, icon previews)
            twin = os.path.join(V1, folder, re.sub(r"(-\d+)?\.png$", ".svg", name))
            alt = svg_info(twin)[2] if os.path.exists(twin) else None
        assets.append({
            "path": f"{folder}/{name}",
            "kind": KINDS[folder],
            "id": m["id"],
            "theme": m["theme"],
            "animated": bool(m["animated"]),
            "format": m["ext"],
            "width": w,
            "height": h,
            "alt": alt,
            "href": links.get(m["id"]),
            "bytes": os.path.getsize(path),
        })
    return {"version": 1, "base": BASE_URL, "assets": assets}

def render():
    return json.dumps(build(), indent=1, ensure_ascii=False) + "\n"

if __name__ == "__main__":
    text = render()
    open(MANIFEST, "w").write(text)
    print(f"wrote {len(json.loads(text)['assets'])} entries to {MANIFEST}")
