#!/usr/bin/env python3
"""Expressive Flow launcher icons.

Each icon is an Android adaptive icon on the standard 108dp canvas:
  background  : a solid colour
  foreground  : an M3 Expressive shape + the F, kept inside the 66dp safe zone
  monochrome  : one-colour version for Android 13+ themed icons

Outputs per icon (in out/icons/<id>/):
  drawable/ic_launcher_<id>_foreground.xml, drawable/ic_launcher_<id>_monochrome.xml
  mipmap-anydpi-v26/ic_launcher_<id>.xml and _round.xml
  <id>.svg (full icon, 108 canvas) and <id>-preview.svg (masked, as a launcher shows it)
plus colors snippet and manifest activity-alias snippet.

  python3 flowicons.py                   # full Android resource set into ./out/icons (not committed)
  python3 flowicons.py --previews-only   # just <id>.svg and <id>-512.png (squircle mask) into ../v1/icons
"""
import os, io, math, json, argparse
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path
import pathops
from flowbadges import shape_path, HERE, FONT, V1
from raster import svg_to_png

def _to_pathops(d):
    p = pathops.Path(); parse_path(d, p.getPen()); return p

def _to_d(p):
    pen = SVGPathPen(None, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
    p.draw(pen); return pen.getCommands()

def union(d):
    """Merge overlapping contours (the F's stem and bars) into one outline."""
    return _to_d(pathops.simplify(_to_pathops(d), fix_winding=True))

def cut(shape_d, hole_d):
    """Shape with the hole removed, as one clean outline (no evenOdd tricks needed)."""
    return _to_d(pathops.op(_to_pathops(shape_d), _to_pathops(hole_d), pathops.PathOp.DIFFERENCE, fix_winding=True))

OUT = os.path.join(HERE, "out", "icons")

# ---------------------------------------------------------------- the F
_font = None
def glyph_F():
    global _font
    if _font is None:
        f = TTFont(FONT)
        _font = instancer.instantiateVariableFont(
            f, {"wght": 900, "wdth": 100, "ROND": 100, "opsz": 144, "GRAD": 0, "slnt": -10})
    return _font

def F_path(cx, cy, cap_h, optical_dx=0.0):
    """Heavy, fully rounded, slanted Google Sans Flex 'F', centred on (cx, cy) with the given cap height."""
    font = glyph_F(); gs = font.getGlyphSet()
    name = font.getBestCmap()[ord("F")]
    bp = BoundsPen(gs); gs[name].draw(bp)
    xmin, ymin, xmax, ymax = bp.bounds
    s = cap_h / (ymax - ymin)
    w = (xmax - xmin) * s
    ox = cx - w / 2 - xmin * s + optical_dx
    oy = cy + cap_h / 2 + ymin * s       # y flips
    pen = SVGPathPen(gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
    gs[name].draw(TransformPen(pen, (s, 0, 0, -s, ox, oy)))
    return union(pen.getCommands())

# ---------------------------------------------------------------- the pill F (built from three rounded strokes)
def pill_F(cx, cy, h, stroke, color, slant=math.radians(11), gap=3.2):
    """Stem + two bars as separate pills with a small gap, like an M3 connected button group."""
    t = math.tan(slant)
    top, bot = cy - h / 2, cy + h / 2
    sx = lambda y, x0: x0 + (cy - y) * t           # slanted x at height y
    stem_x = cx - h * 0.26
    r = stroke / 2
    segs = [
        ((sx(bot - r, stem_x), bot - r), (sx(top + r, stem_x), top + r)),                      # stem
        ((sx(top + r, stem_x) + stroke + gap, top + r), (sx(top + r, stem_x) + h * 0.74, top + r)),   # top bar
        ((sx(cy + 1.5, stem_x) + stroke + gap, cy + 1.5), (sx(cy + 1.5, stem_x) + h * 0.56, cy + 1.5)),       # middle bar
    ]
    return [("stroke", f"M{a[0]:.2f} {a[1]:.2f}L{b[0]:.2f} {b[1]:.2f}", color, stroke) for a, b in segs]

def play_path(cx, cy, size, rr=0.18):
    """Rounded play triangle."""
    pts = [(cx - size * 0.38, cy - size * 0.5), (cx + size * 0.55, cy), (cx - size * 0.38, cy + size * 0.5)]
    k = rr
    d = []
    for i in range(3):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % 3]
        a = (p1[0] + (p0[0] - p1[0]) * k, p1[1] + (p0[1] - p1[1]) * k)
        b = (p1[0] + (p2[0] - p1[0]) * k, p1[1] + (p2[1] - p1[1]) * k)
        d.append(("M" if i == 0 else "L") + f"{a[0]:.2f} {a[1]:.2f}Q{p1[0]:.2f} {p1[1]:.2f} {b[0]:.2f} {b[1]:.2f}")
    return "".join(d) + "Z"

# ---------------------------------------------------------------- M3 Oval and Pill (not polar, so built from outlines)
def _rot(pts, cx, cy, ang):
    c, s_ = math.cos(ang), math.sin(ang)
    return [(cx + (x - cx) * c - (y - cy) * s_, cy + (x - cx) * s_ + (y - cy) * c) for x, y in pts]

def oval_path(cx, cy, a, b, ang=-math.pi / 4, n=96):
    """M3 'Oval': an ellipse tilted 45 degrees."""
    pts = [(cx + a * math.cos(2 * math.pi * i / n), cy + b * math.sin(2 * math.pi * i / n)) for i in range(n)]
    from flowbadges import _smooth_closed
    return _smooth_closed(_rot(pts, cx, cy, ang))

def pill_shape_path(cx, cy, a, b, ang=-math.pi / 4):
    """M3 'Pill': a short capsule (stadium) tilted 45 degrees. a = half length, b = half width (end radius)."""
    L = a - b
    k = 0.5523 * b   # cubic arc constant
    # capsule along x, built from two straight edges and two semicircles (4 cubic quarter arcs)
    P = [
        ("M", [(cx - L, cy - b)]),
        ("L", [(cx + L, cy - b)]),
        ("C", [(cx + L + k, cy - b), (cx + L + b, cy - k), (cx + L + b, cy)]),
        ("C", [(cx + L + b, cy + k), (cx + L + k, cy + b), (cx + L, cy + b)]),
        ("L", [(cx - L, cy + b)]),
        ("C", [(cx - L - k, cy + b), (cx - L - b, cy + k), (cx - L - b, cy)]),
        ("C", [(cx - L - b, cy - k), (cx - L - k, cy - b), (cx - L, cy - b)]),
    ]
    out = []
    for cmd, pts in P:
        pts = _rot(pts, cx, cy, ang)
        out.append(cmd + " ".join(f"{x:.2f} {y:.2f}" for x, y in pts))
    return "".join(out) + "Z"

def circle_path(cx, cy, r):
    k = 0.5523 * r
    return (f"M{cx - r:.2f} {cy:.2f}C{cx - r:.2f} {cy - k:.2f} {cx - k:.2f} {cy - r:.2f} {cx:.2f} {cy - r:.2f}"
            f"C{cx + k:.2f} {cy - r:.2f} {cx + r:.2f} {cy - k:.2f} {cx + r:.2f} {cy:.2f}"
            f"C{cx + r:.2f} {cy + k:.2f} {cx + k:.2f} {cy + r:.2f} {cx:.2f} {cy + r:.2f}"
            f"C{cx - k:.2f} {cy + r:.2f} {cx - r:.2f} {cy + k:.2f} {cx - r:.2f} {cy:.2f}Z")

# ---------------------------------------------------------------- designs
C, R = 54, 31   # canvas centre, shape radius (inside the 33dp safe-zone radius)

def designs():
    return [
        {"id": "expressive_scallop", "name": "Scallop", "alias": "IconExpressiveScallop",
         "note": "The main candidate. Flow red scallop on a soft red background, heavy rounded F.",
         "bg": "#FFDAD4",
         "fg": [("fill", shape_path("cookie9", C, C, R), "#EB0000", None),
                ("fill", F_path(C, C, 27, optical_dx=0.6), "#FFFFFF", None)],
         "mono": [("fill", cut(shape_path("cookie9", C, C, R), F_path(C, C, 27, optical_dx=0.6)), "#FFFFFF", None)]},

        {"id": "expressive_pill", "name": "Segmented F", "alias": "IconExpressivePill",
         "note": "The F rebuilt from three rounded pills with small gaps, the same idea as the info chips. Closest to a new wordmark.",
         "bg": "#EB0000",
         "fg": pill_F(C, C, 36, 11.5, "#FFFFFF"),
         "mono": pill_F(C, C, 36, 11.5, "#FFFFFF")},

        {"id": "expressive_play", "name": "Sunny Play", "alias": "IconExpressivePlay",
         "note": "An Expressive take on the Flow Play icon. Coral sunny shape and a rounded play mark on a warm dark background.",
         "bg": "#2B1613",
         "fg": [("fill", shape_path("sunny", C, C, R), "#FF5540", None),
                ("fill", play_path(C + 1.5, C, 24), "#360000", None)],
         "mono": [("fill", cut(shape_path("sunny", C, C, R), play_path(C + 1.5, C, 24)), "#FFFFFF", None)]},

        {"id": "expressive_sky", "name": "Sky Clover", "alias": "IconExpressiveSky",
         "note": "An Expressive version of Material Sky. Blue clover, white F.",
         "bg": "#D7E3FF",
         "fg": [("fill", shape_path("clover4", C, C, R + 1, rot=math.pi / 4), "#0059BA", None),
                ("fill", F_path(C, C, 25, optical_dx=0.6), "#FFFFFF", None)],
         "mono": [("fill", cut(shape_path("clover4", C, C, R + 1, rot=math.pi / 4), F_path(C, C, 25, optical_dx=0.6)), "#FFFFFF", None)]},

        {"id": "expressive_mint", "name": "Mint Flower", "alias": "IconExpressiveMint",
         "note": "An Expressive version of Material Mint. Green flower, white F.",
         "bg": "#C7E8D4",
         "fg": [("fill", shape_path("flower", C, C, R + 1, rot=math.pi / 8), "#006C4C", None),
                ("fill", F_path(C, C, 25, optical_dx=0.6), "#FFFFFF", None)],
         "mono": [("fill", cut(shape_path("flower", C, C, R + 1, rot=math.pi / 8), F_path(C, C, 25, optical_dx=0.6)), "#FFFFFF", None)]},

        {"id": "expressive_amoled", "name": "Night Cookie", "alias": "IconExpressiveAmoled",
         "note": "For AMOLED users. Pure black background, red 12-sided cookie with a black F cut out.",
         "bg": "#000000",
         "fg": [("fill", cut(shape_path("cookie12", C, C, R), F_path(C, C, 27, optical_dx=0.6)), "#FF1A1A", None)],
         "mono": [("fill", cut(shape_path("cookie12", C, C, R), F_path(C, C, 27, optical_dx=0.6)), "#FFFFFF", None)]},

        {"id": "expressive_oval", "name": "Oval", "alias": "IconExpressiveOval",
         "note": "The M3 Oval, tilted 45 degrees. A white oval on Flow red with a red F, so it reads as the inverse of Scallop.",
         "bg": "#EB0000",
         "fg": [("fill", oval_path(C, C, 33, 22.5), "#FFFFFF", None),
                ("fill", F_path(C, C, 24, optical_dx=0.4), "#EB0000", None)],
         "mono": [("fill", cut(oval_path(C, C, 33, 22.5), F_path(C, C, 24, optical_dx=0.4)), "#FFFFFF", None)]},

        {"id": "expressive_pillshape", "name": "Pill", "alias": "IconExpressivePillShape",
         "note": "The M3 Pill, a short capsule tilted 45 degrees. Flow red on a near-white background, closest to a stock Material app icon.",
         "bg": "#FFF8F6",
         "fg": [("fill", pill_shape_path(C, C, 32.5, 25), "#EB0000", None),
                ("fill", F_path(C, C, 26, optical_dx=0.5), "#FFFFFF", None)],
         "mono": [("fill", cut(pill_shape_path(C, C, 32.5, 25), F_path(C, C, 26, optical_dx=0.5)), "#FFFFFF", None)]},
    ]

# ---------------------------------------------------------------- nightly
NIGHT_BG, MOON_BADGE, MOON = "#17153A", "#C5C0FF", "#2A2470"
BX, BY, BR, GAP = 71, 71, 10.5, 2.4       # badge sits bottom-right, inside the 33dp safe zone
NS, NT = 0.86, -3.2                        # main design shrinks a little and moves up-left to make room

def xf_d(d, s, t):
    pen = SVGPathPen(None, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
    parse_path(d, TransformPen(pen, (s, 0, 0, s, C - C * s + t, C - C * s + t)))
    return pen.getCommands()

def crescent(cx, cy, r):
    return cut(circle_path(cx, cy, r), circle_path(cx + r * 0.55, cy - r * 0.45, r * 0.88))

def nightly(ic):
    """Same design at night: deep indigo background and a moon badge on the Nightly cookie shape."""
    ring = circle_path(BX, BY, BR + GAP)
    badge = shape_path("cookie6", BX, BY, BR)
    moon = crescent(BX - 0.8, BY + 0.6, BR * 0.6)
    def adapt(elems):
        out = []
        for k, d, col, x in elems:
            d2 = xf_d(d, NS, NT)
            if k == "fill":
                out.append((k, cut(d2, ring), col, x))
            else:
                out.append((k, d2, col, round(x * NS, 2)))
        return out
    return {
        "id": ic["id"] + "_nightly", "name": ic["name"] + " Nightly", "alias": ic["alias"] + "Nightly",
        "note": "Nightly version of " + ic["name"] + ".", "bg": NIGHT_BG, "nightly": True, "base": ic["id"],
        "fg": adapt(ic["fg"]) + [("fill", badge, MOON_BADGE, None), ("fill", moon, MOON, None)],
        "mono": adapt(ic["mono"]) + [("fill", cut(badge, moon), "#FFFFFF", None)],
    }

# ---------------------------------------------------------------- writers
def svg_elems(elems):
    out = []
    for kind, d, color, extra in elems:
        if kind == "fill":
            fr = ' fill-rule="evenodd"' if extra == "evenOdd" else ""
            out.append(f'<path d="{d}" fill="{color}"{fr}/>')
        else:
            out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{extra}" stroke-linecap="round"/>')
    return "".join(out)

def vd_elems(elems, mono=False):
    out = []
    for kind, d, color, extra in elems:
        col = "#FFFFFFFF" if mono else "#FF" + color.lstrip("#").upper()
        if kind == "fill":
            ft = '\n        android:fillType="evenOdd"' if extra == "evenOdd" else ""
            out.append(f'    <path\n        android:fillColor="{col}"{ft}\n        android:pathData="{d}" />')
        else:
            out.append(f'    <path\n        android:strokeColor="{col}"\n        android:strokeWidth="{extra}"\n'
                       f'        android:strokeLineCap="round"\n        android:pathData="{d}" />')
    return "\n".join(out)

def vector(elems, mono=False):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
            '    android:width="108dp"\n    android:height="108dp"\n'
            '    android:viewportWidth="108"\n    android:viewportHeight="108">\n'
            + vd_elems(elems, mono) + "\n</vector>\n")

MASKS = {
    "circle": '<circle cx="54" cy="54" r="36"/>',
    "squircle": None,   # generated
    "rounded": '<rect x="18" y="18" width="72" height="72" rx="17"/>',
}
def squircle():
    pts = []
    for i in range(200):
        t = 2 * math.pi * i / 200
        c, s = math.cos(t), math.sin(t)
        x = 36 * abs(c) ** (2 / 5) * (1 if c >= 0 else -1)
        y = 36 * abs(s) ** (2 / 5) * (1 if s >= 0 else -1)
        pts.append(f"{54 + x:.2f} {54 + y:.2f}")
    return f'<path d="M{"L".join(pts)}Z"/>'
MASKS["squircle"] = squircle()

def full_svg(ic, mask=None, themed=None):
    """themed = (bg, fg) to preview the monochrome layer tinted the way Android 13+ does."""
    if themed:
        body = f'<rect width="108" height="108" fill="{themed[0]}"/>' + svg_elems(
            [(k, d, themed[1], x) for k, d, _, x in ic["mono"]])
    else:
        body = f'<rect width="108" height="108" fill="{ic["bg"]}"/>' + svg_elems(ic["fg"])
    if mask:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="18 18 72 72" width="192" height="192">'
                f'<defs><clipPath id="m">{MASKS[mask]}</clipPath></defs><g clip-path="url(#m)">{body}</g></svg>\n')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="432" height="432">{body}</svg>\n'

def preview_svg(ic):
    """The full 108 canvas icon, labelled so it passes the same checks as the badges."""
    label = f'Flow launcher icon: {ic["name"]}'
    return full_svg(ic).replace(' width="432" height="432">',
                                f' width="432" height="432" role="img" aria-label="{label}"><title>{label}</title>', 1)

def previews_only():
    out = os.path.join(V1, "icons")
    os.makedirs(out, exist_ok=True)
    base = designs()
    for ic in base + [nightly(i) for i in base]:
        open(os.path.join(out, f'{ic["id"]}.svg'), "w").write(preview_svg(ic))
        svg_to_png(full_svg(ic, "squircle"), os.path.join(out, f'{ic["id"]}-512.png'), 512, 512)
    print("icon previews written to", out)

def main():
    os.makedirs(OUT, exist_ok=True)
    colors, aliases, manifest = [], [], []
    base = designs()
    ALL = base + [nightly(i) for i in base]
    for ic in ALL:
        d = os.path.join(OUT, ic["id"])
        for sub in ("drawable", "mipmap-anydpi-v26", "preview"):
            os.makedirs(os.path.join(d, sub), exist_ok=True)
        open(os.path.join(d, "drawable", f'ic_launcher_{ic["id"]}_foreground.xml'), "w").write(vector(ic["fg"]))
        open(os.path.join(d, "drawable", f'ic_launcher_{ic["id"]}_monochrome.xml'), "w").write(vector(ic["mono"], True))
        adaptive = ('<?xml version="1.0" encoding="utf-8"?>\n'
                    '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                    f'    <background android:drawable="@color/icon_bg_{ic["id"]}" />\n'
                    f'    <foreground android:drawable="@drawable/ic_launcher_{ic["id"]}_foreground" />\n'
                    f'    <monochrome android:drawable="@drawable/ic_launcher_{ic["id"]}_monochrome" />\n'
                    '</adaptive-icon>\n')
        for suffix in ("", "_round"):
            open(os.path.join(d, "mipmap-anydpi-v26", f'ic_launcher_{ic["id"]}{suffix}.xml'), "w").write(adaptive)
        open(os.path.join(d, f'{ic["id"]}.svg'), "w").write(full_svg(ic))
        for m in MASKS:
            open(os.path.join(d, "preview", f"{m}.svg"), "w").write(full_svg(ic, m))
        open(os.path.join(d, "preview", "themed-light.svg"), "w").write(full_svg(ic, "circle", ("#D8E2FF", "#1B2D4F")))
        open(os.path.join(d, "preview", "themed-dark.svg"), "w").write(full_svg(ic, "circle", ("#1B2D4F", "#D8E2FF")))
        if ic.get("nightly"):
            continue
        colors.append(f'    <color name="icon_bg_{ic["id"]}">{ic["bg"]}</color>')
        manifest.append(f'''        <!-- {ic["name"]} (Expressive) -->
        <activity-alias
            android:name=".{ic["alias"]}"
            android:enabled="false"
            android:exported="true"
            android:icon="@mipmap/ic_launcher_{ic["id"]}"
            android:roundIcon="@mipmap/ic_launcher_{ic["id"]}_round"
            android:targetActivity=".MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>''')
    open(os.path.join(OUT, "colors_snippet.xml"), "w").write("<!-- add to res/values/colors.xml -->\n" + "\n".join(colors) + "\n")
    open(os.path.join(OUT, "manifest_snippet.xml"), "w").write("<!-- add next to the other icon aliases in AndroidManifest.xml -->\n" + "\n\n".join(manifest) + "\n")
    json.dump([{k: ic.get(k) for k in ("id", "name", "alias", "note", "bg", "nightly", "base")} for ic in ALL],
              open(os.path.join(OUT, "icons.json"), "w"), indent=1)
    print("icons written to", OUT)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--previews-only", action="store_true", help="write only the SVG and 512px PNG previews into v1/icons")
    previews_only() if ap.parse_args().previews_only else main()
