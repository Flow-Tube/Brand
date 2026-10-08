#!/usr/bin/env python3
"""Flow banners: README headers (1280x420, SVG) and GitHub social previews (1280x640).

Same system as flowbadges.py: Flow tonal palette, outlined Google Sans Flex, M3 Expressive shapes.
Each feature shape carries an icon, so the right-hand cluster doubles as a feature summary.
"""
import json, os, math
from flowbadges import text_outline, text_width, icon_svg, shape_path, wrap, PALETTE, HERE, V1
from raster import svg_to_png

BANNERS = json.load(open(os.path.join(HERE, "banners.json")))

def fit(text, size, maxw, **kw):
    while text_width(text, size, **kw) > maxw and size > 20:
        size -= 2
    return size

def chip(x, y, label, P, h=42):
    tw = text_width(label, 18, wght=600)
    w = tw + 36
    d, _ = text_outline(label, 18, x + 18, y + h / 2 + 6.5, wght=600)
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{P["surfaceContainerHighest"]}"/>'
            f'<path fill="{P["onSurfaceVariant"]}" d="{d}"/>'), w

def render(b, theme, W, H, rounded, animated):
    P = PALETTE[theme]
    s = 1.25 if H > 420 else 1.0             # cluster scale for the taller social card
    body = []
    body.append(f'<rect width="{W}" height="{H}" rx="{56 if rounded else 0}" fill="{P["surfaceContainer"]}"/>')

    # ---- right cluster: four feature shapes, each a different M3 shape and container colour
    roles = {
        "primary":   (P["primaryContainer"], P["onPrimaryContainer"]),
        "tertiary":  (P["tertiaryContainer"], P["onTertiaryContainer"]),
        "secondary": (P["secondaryContainer"], P["onSecondaryContainer"]),
        "neutral":   (P["surfaceContainerHighest"], P["primary"]),
    }
    cx0, cy0 = W - 250 * s, H / 2
    css = []
    for i, f in enumerate(b["features"]):
        fx, fy = cx0 + f["dx"] * s, cy0 + f["dy"] * s
        R = f["r"] * s
        fill, on = roles[f["role"]]
        body.append(f'<path class="f{i}" fill="{fill}" d="{shape_path(f["shape"], fx, fy, R)}"/>')
        body.append(icon_svg(f["icon"], fx, fy, R * 0.82, on))
        if animated:
            dur, dirn = f.get("spin", 40), "" if i % 2 == 0 else "reverse"
            css.append(f".f{i}{{transform-origin:{fx:.1f}px {fy:.1f}px;animation:spin {dur}s linear infinite {dirn}}}")

    # ---- left block: mark + title, tagline lines, chips
    left = 72 if H <= 420 else 88
    maxw = cx0 - 215 * s - left   # keep clear of the shape cluster
    mark_R = 62 if H <= 420 else 78
    title_size = fit(b["title"], 132 if H <= 420 else 150, maxw - mark_R * 2 - 28, wght=800)
    tag_size = 28 if H <= 420 else 34
    tag_size = min(fit(ln, tag_size, maxw, wght=500) for ln in b["tagline"])
    line_h = tag_size * 1.32
    block_h = mark_R * 2 + 26 + len(b["tagline"]) * line_h + 22 + 42
    top = (H - block_h) / 2

    mcx, mcy = left + mark_R, top + mark_R
    body.append(f'<path class="mk" fill="#FFFFFF" d="{shape_path("cookie12", mcx, mcy, mark_R)}"/>')
    body.append(icon_svg("flow", mcx, mcy + 1, mark_R * 1.25, None))
    if animated:
        css.append(f".mk{{transform-origin:{mcx:.1f}px {mcy:.1f}px;animation:spin 60s linear infinite}}")
    tx = left + mark_R * 2 + 28
    td, _ = text_outline(b["title"], title_size, tx, mcy + title_size * 0.36, wght=800, wdth=100)
    body.append(f'<path fill="{P["onSurface"]}" d="{td}"/>')

    y = top + mark_R * 2 + 26 + tag_size
    for ln in b["tagline"]:
        d, _ = text_outline(ln, tag_size, left, y, wght=500)
        body.append(f'<path fill="{P["onSurfaceVariant"]}" d="{d}"/>')
        y += line_h
    x, cy = left, y - tag_size + 22
    for c in b["chips"]:
        svg, w = chip(x, cy, c, P)
        body.append(svg); x += w + 10

    style = ""
    if css:
        style = "".join(css) + "@keyframes spin{to{transform:rotate(360deg)}}"
    return wrap(W, H, "".join(body), f'{b["title"]}. {" ".join(b["tagline"])}', style)

def main():
    out = os.path.join(V1, "banners")
    os.makedirs(out, exist_ok=True)
    n = 0
    for b in BANNERS:
        for theme in ("light", "dark"):
            for anim in (False, True):
                svg = render(b, theme, 1280, 420, True, anim)
                open(os.path.join(out, f'{b["id"]}-{theme}{"-animated" if anim else ""}.svg'), "w").write(svg); n += 1
            svg = render(b, theme, 1280, 640, False, False)
            open(os.path.join(out, f'{b["id"]}-social-{theme}.svg'), "w").write(svg); n += 1
            svg_to_png(svg, os.path.join(out, f'{b["id"]}-social-{theme}.png'), 1280, 640); n += 1
    print(f"wrote {n} banner files to {out}")

if __name__ == "__main__":
    main()
