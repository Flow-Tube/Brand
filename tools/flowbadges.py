#!/usr/bin/env python3
"""
Flow badge generator.

Builds Material 3 Expressive badges for the Flow projects as self-contained SVGs:
  * text is converted to outlines (Google Sans Flex, ROND 100) so it renders the same
    everywhere, including GitHub, which blocks web fonts inside <img> SVGs
  * colours come from an M3 "fidelity" tonal scheme seeded with Flow red (#FF0000)
  * every badge ships as -light and -dark files, meant for <picture> + prefers-color-scheme

Styles
  pill   : big two-line "Get it on" button, icon inside an M3 Expressive shape
  split  : connected button group, the replacement for shields.io style chips
  tile   : square tile with a large expressive shape, for org/website grids

Usage
  python3 flowbadges.py                     # renders everything in badges.json into ../v1/badges
  python3 flowbadges.py --set downloads=48k # override a value (handy in CI)
  python3 flowbadges.py --only release,downloads --set release=v3.0  # render just those ids
"""
import json, math, os, re, sys, argparse, functools
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import uharfbuzz as hb

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "gsf.ttf")
V1 = os.path.join(HERE, "..", "v1")
ICON_DIRS = {
    "si": os.path.join(HERE, "node_modules", "simple-icons", "icons"),
    "ms": os.path.join(HERE, "node_modules", "@material-symbols", "svg-600", "rounded"),
}
PALETTE = json.load(open(os.path.join(HERE, "palette.json")))
FLOW_RED = "#FF0000"

# ----------------------------------------------------------------------------- text
@functools.lru_cache(maxsize=None)
def _instance(wght, wdth, rond, opsz):
    f = TTFont(FONT)
    inst = instancer.instantiateVariableFont(
        f, {"wght": wght, "wdth": wdth, "ROND": rond, "opsz": opsz, "GRAD": 0, "slnt": 0})
    import io
    buf = io.BytesIO(); inst.save(buf)
    data = buf.getvalue()
    return TTFont(io.BytesIO(data)), data

def text_outline(text, size, x, baseline, wght=500, wdth=100, rond=100, track=0.0):
    """Return (svg path d, advance width in px). track is in em."""
    # optical size follows px size, snapped to a few steps so font instances can be cached
    opsz = min((12, 14, 17, 18, 21, 24, 32, 48, 72, 96, 144), key=lambda o: abs(o - size))
    font, data = _instance(wght, wdth, rond, opsz)
    upem = font["head"].unitsPerEm
    scale = size / upem
    face = hb.Face(data); hfont = hb.Font(face)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(hfont, buf, {"kern": True, "liga": True})
    gs = font.getGlyphSet(); order = font.getGlyphOrder()
    pen = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
    cx = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        t = TransformPen(pen, (scale, 0, 0, -scale, x + (cx + pos.x_offset) * scale, baseline - pos.y_offset * scale))
        gs[name].draw(t)
        cx += pos.x_advance + track * upem
    return relative_d(pen.getCommands()), (cx - track * upem) * scale

_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "Q": 4, "C": 6, "Z": 0}

def relative_d(d):
    """Rewrite absolute path data on the 0.1px grid as relative commands, about a third shorter.
    Deltas are taken between the already-rounded points, so the geometry is unchanged."""
    toks = re.findall(r"[MLHVQCZ]|-?\d*\.?\d+", d)
    out, cmd, i = [], None, 0
    x = y = sx = sy = 0                      # current point and subpath start, in tenths
    def num(v):
        s = str(v // 10) if v % 10 == 0 else ("%.1f" % (v / 10))
        return s.replace("0.", ".", 1) if s.lstrip("-").startswith("0.") else s
    def emit(c, vals):
        s = "".join((" " if j and not num(v).startswith("-") else "") + num(v) for j, v in enumerate(vals))
        out.append(c + s)
    while i < len(toks):
        if toks[i] in _ARGS:
            cmd = toks[i]; i += 1
            if cmd == "Z":
                out.append("z"); x, y = sx, sy
                continue
        elif cmd == "M":
            cmd = "L"                         # implicit lineto after a moveto
        n = _ARGS[cmd]
        v = [round(float(t) * 10) for t in toks[i:i + n]]; i += n
        if cmd == "H":
            emit("h", [v[0] - x]); x = v[0]
        elif cmd == "V":
            emit("v", [v[0] - y]); y = v[0]
        else:
            emit(cmd.lower(), [c - (x if k % 2 == 0 else y) for k, c in enumerate(v)])
            x, y = v[-2], v[-1]
            if cmd == "M":
                sx, sy = x, y
    return "".join(out)

def text_width(text, size, **kw):
    return text_outline(text, size, 0, 0, **kw)[1]

# ----------------------------------------------------------------------------- icons
def load_icon(ref):
    """ref = 'si:github' | 'ms:android' | 'flow'. Returns (viewBox tuple, inner svg paths)."""
    if ref == "flow":
        return (0, 0, 24, 24), None
    kind, name = ref.split(":")
    path = os.path.join(ICON_DIRS[kind], name + ("-fill.svg" if kind == "ms" else ".svg"))
    s = open(path).read()
    vb = tuple(float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split())
    ds = re.findall(r'<path[^>]* d="([^"]+)"', s)
    return vb, ds

def icon_svg(ref, cx, cy, size, fill):
    if ref == "flow":  # the Flow mark, in its own colours
        s = size / 24.0
        return (f'<g transform="translate({cx - size/2:.2f} {cy - size/2:.2f}) scale({s:.4f})">'
                f'<path fill="{FLOW_RED}" d="M21.58 7.16C21.33 6.22 20.59 5.48 19.65 5.23C17.96 4.77 12 4.77 12 4.77C12 4.77 6.04 4.77 4.35 5.23C3.41 5.48 2.67 6.22 2.42 7.16C1.96 8.85 1.96 12.38 1.96 12.38C1.96 12.38 1.96 15.91 2.42 17.6C2.67 18.54 3.41 19.28 4.35 19.53C6.04 19.99 12 19.99 12 19.99C12 19.99 17.96 19.99 19.65 19.530C20.59 19.28 21.33 18.54 21.58 17.6C22.04 15.91 22.04 12.38 22.04 12.38C22.04 12.38 22.04 8.85 21.58 7.16Z"/>'
                f'<path fill="#FFFFFF" d="M10 7L18 7L17.2 9.5H12.8L12.2 11.5H16L15.2 14H11.5L10.5 17H7.5L10 7Z"/></g>')
    (vx, vy, vw, vh), ds = load_icon(ref)
    s = size / max(vw, vh)
    return (f'<g fill="{fill}" transform="translate({cx - size/2:.2f} {cy - size/2:.2f}) scale({s:.5f}) translate({-vx} {-vy})">'
            + "".join(f'<path d="{d}"/>' for d in ds) + "</g>")

# ----------------------------------------------------------------------------- M3 Expressive shapes
def _smooth_closed(pts):
    """Catmull-Rom through points -> closed cubic bezier path."""
    n = len(pts); d = [f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"]
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return "".join(d) + "Z"

def _polar(fn, cx, cy, R, rot=0.0, samples=90):
    pts = []
    for i in range(samples):
        t = 2 * math.pi * i / samples
        r = R * fn(t)
        pts.append((cx + r * math.cos(t + rot), cy + r * math.sin(t + rot)))
    return pts

def _norm(fn):
    m = max(fn(2 * math.pi * i / 720) for i in range(720))
    return lambda t: fn(t) / m

SHAPES = {
    # approximations of the androidx.graphics.shapes MaterialShapes library
    "cookie9":  _norm(lambda t: 1 + 0.075 * math.cos(9 * t)),
    "cookie12": _norm(lambda t: 1 + 0.06 * math.cos(12 * t)),
    "cookie6":  _norm(lambda t: 1 + 0.09 * math.cos(6 * t)),
    "clover4":  _norm(lambda t: 0.70 + 0.30 * abs(math.cos(2 * t)) ** 0.55),
    "sunny":    _norm(lambda t: 1 + 0.10 * (abs(math.cos(4 * t)) ** 3 * 2 - 1)),
    "flower":   _norm(lambda t: 0.80 + 0.20 * abs(math.cos(4 * t)) ** 0.7),
    "circle":   lambda t: 1.0,
}

def shape_path(kind, cx, cy, R, rot=0.0):
    if kind == "heart":
        s = R / 12.0
        pts = []
        for i in range(160):
            t = 2 * math.pi * i / 160
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            pts.append((cx + x * s * 0.72, cy + (y + 1.5) * s * 0.72))
        return _smooth_closed(pts)
    return _smooth_closed(_polar(SHAPES[kind], cx, cy, R, rot))

CATEGORY_SHAPE = {"download": "cookie9", "community": "clover4", "support": "heart",
                  "info": "sunny", "brand": "cookie12", "project": "flower", "nightly": "cookie6"}

# ----------------------------------------------------------------------------- svg wrapper
def wrap(w, h, body, label, anim_css=""):
    esc = label.replace("&", "&amp;").replace("<", "&lt;")
    style = ""
    if anim_css:
        style = ("<style>" + anim_css +
                 "@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
            f'viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="{esc}"><title>{esc}</title>{style}{body}</svg>\n')

# ----------------------------------------------------------------------------- style: pill
def render_pill(b, theme, animated=False):
    P = PALETTE[theme]
    H, pad_l, shape_d, gap, pad_r = 60, 8, 44, 12, 26
    cat = b.get("category", "download")
    over, label = b["overline"], b["label"]
    ow = text_width(over, 12.5, wght=500, track=0.02)
    lw = text_width(label, 21, wght=720, wdth=100)
    tx = pad_l + shape_d + gap
    W = math.ceil(tx + max(ow, lw) + pad_r)
    # emphasis: "filled" puts the whole button in the brand colour
    filled = b.get("emphasis") == "filled"
    bg = P["primaryContainer"] if filled else P["surfaceContainerHigh"]
    on_bg = P["onPrimaryContainer"] if filled else P["onSurface"]
    on_bg_var = P["onPrimaryContainer"] if filled else P["onSurfaceVariant"]
    shape_fill = P["onPrimaryContainer"] if filled else P["primaryContainer"]
    icon_fill = P["primaryContainer"] if filled else P["onPrimaryContainer"]
    if cat == "brand":
        shape_fill = "#FFFFFF"  # the Flow mark sits on white, like the light app icon
    cx, cy = pad_l + shape_d / 2, H / 2
    kind = CATEGORY_SHAPE.get(cat, "cookie9")
    shape = f'<path class="s" fill="{shape_fill}" d="{shape_path(kind, cx, cy, shape_d / 2)}"/>'
    css = ""
    if animated and kind != "heart":
        css = (f".s{{transform-origin:{cx}px {cy}px;animation:spin 18s linear infinite}}"
               "@keyframes spin{to{transform:rotate(360deg)}}")
    elif animated:
        css = (f".s{{transform-origin:{cx}px {cy}px;animation:beat 2.4s ease-in-out infinite}}"
               "@keyframes beat{0%,100%{transform:scale(1)}12%{transform:scale(1.08)}24%{transform:scale(1)}}")
    icon = icon_svg(b["icon"], cx, cy + (1 if kind == "heart" else 0), 22 if kind != "heart" else 18, icon_fill)
    od, _ = text_outline(over, 12.5, tx, 25.5, wght=500, track=0.02)
    ld, _ = text_outline(label, 21, tx, 46, wght=720)
    body = (f'<rect width="{W}" height="{H}" rx="{H/2}" fill="{bg}"/>' + shape + icon +
            f'<path fill="{on_bg_var}" d="{od}"/><path fill="{on_bg}" d="{ld}"/>')
    return wrap(W, H, body, f"{over} {label}", css)

# ----------------------------------------------------------------------------- style: split (button group)
def render_split(b, theme, animated=False):
    P = PALETTE[theme]
    H, gap, outer, inner = 32, 3, 16, 5
    key, val = b["key"], b["value"]
    kw_ = text_width(key, 13.5, wght=600)
    vw_ = text_width(val, 13.5, wght=760)
    icon_sz = 18
    lw = 10 + icon_sz + 6 + kw_ + 12
    rw = 12 + vw_ + 14
    W = math.ceil(lw + gap + rw)
    kfill, kon = P["primary"], P["onPrimary"]
    vfill, von = P["surfaceContainerHighest"], P["onSurface"]
    def seg(x, w, rl, rr, fill):
        # rect with different left/right radii (M3 connected button group)
        return (f'<path fill="{fill}" d="M{x+rl} 0H{x+w-rr}A{rr} {rr} 0 0 1 {x+w} {rr}V{H-rr}A{rr} {rr} 0 0 1 {x+w-rr} {H}'
                f'H{x+rl}A{rl} {rl} 0 0 1 {x} {H-rl}V{rl}A{rl} {rl} 0 0 1 {x+rl} 0Z"/>')
    body = seg(0, lw, outer, inner, kfill) + seg(lw + gap, rw, inner, outer, vfill)
    body += icon_svg(b["icon"], 10 + icon_sz / 2, H / 2, icon_sz, kon)
    kd, _ = text_outline(key, 13.5, 10 + icon_sz + 6, 21, wght=600)
    vd, _ = text_outline(val, 13.5, lw + gap + 12, 21, wght=760)
    body += f'<path fill="{kon}" d="{kd}"/><path fill="{von}" d="{vd}"/>'
    return wrap(W, H, body, f"{key}: {val}")

# ----------------------------------------------------------------------------- style: tile
def render_tile(b, theme, animated=False):
    P = PALETTE[theme]
    W = H = 152
    cat = b.get("category", "project")
    kind = CATEGORY_SHAPE.get(cat, "flower")
    title, sub = b["label"], b.get("sub", b.get("overline", ""))
    cx, cy, R = W / 2, 60, 36
    shape_fill = P["primaryContainer"] if cat != "brand" else "#FFFFFF"
    icon_fill = P["onPrimaryContainer"]
    css = ""
    if animated and kind != "heart":
        css = (f".s{{transform-origin:{cx}px {cy}px;animation:spin 24s linear infinite}}"
               "@keyframes spin{to{transform:rotate(360deg)}}")
    body = f'<rect width="{W}" height="{H}" rx="36" fill="{P["surfaceContainerHigh"]}"/>'
    body += f'<path class="s" fill="{shape_fill}" d="{shape_path(kind, cx, cy, R)}"/>'
    body += icon_svg(b["icon"], cx, cy, 30 if cat != "brand" else 36, icon_fill)
    # scale down long titles to fit
    size = 17
    while text_width(title, size, wght=720) > W - 24 and size > 11:
        size -= 0.5
    tw = text_width(title, size, wght=720)
    td, _ = text_outline(title, size, (W - tw) / 2, 120, wght=720)
    sw = text_width(sub, 11.5, wght=500)
    sd, _ = text_outline(sub, 11.5, (W - sw) / 2, 137, wght=500)
    body += f'<path fill="{P["onSurface"]}" d="{td}"/><path fill="{P["onSurfaceVariant"]}" d="{sd}"/>'
    return wrap(W, H, body, f"{title} {sub}".strip(), css)

RENDER = {"pill": render_pill, "split": render_split, "tile": render_tile}

# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "badges.json"))
    ap.add_argument("--out", default=os.path.join(V1, "badges"))
    ap.add_argument("--set", action="append", default=[], help="id=value override for split badges")
    ap.add_argument("--only", default="", help="comma-separated ids to render (default: all)")
    a = ap.parse_args()
    only = {i for i in a.only.split(",") if i}
    cfg = json.load(open(a.config))
    over = dict(s.split("=", 1) for s in a.set)
    n = 0
    for style, items in cfg.items():
        os.makedirs(os.path.join(a.out, style), exist_ok=True)
        for b in items:
            if only and b["id"] not in only:
                continue
            if b["id"] in over:
                b["value"] = over[b["id"]]
            for theme in ("light", "dark"):
                for anim in ((False, True) if b.get("animated") else (False,)):
                    svg = RENDER[style](b, theme, anim)
                    name = f'{b["id"]}-{theme}{"-animated" if anim else ""}.svg'
                    open(os.path.join(a.out, style, name), "w").write(svg)
                    n += 1
    print(f"wrote {n} files to {a.out}")

if __name__ == "__main__":
    main()
