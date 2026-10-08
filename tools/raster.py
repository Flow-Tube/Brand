"""SVG -> PNG for the social previews and icon previews.

resvg is a pinned pip wheel with no system libraries or browser, so CI renders the same pixels
everywhere. Our SVGs are plain filled paths (text is outlined), which resvg handles exactly.
"""
import resvg_py

def svg_to_png(svg, path, width, height):
    png = resvg_py.svg_to_bytes(svg_string=svg, width=width, height=height, skip_system_fonts=True)
    with open(path, "wb") as f:
        f.write(bytes(png))
