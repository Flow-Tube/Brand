#!/usr/bin/env python3
"""Flow star history chart, in the same M3 Expressive system as the badges and banners.

Data: GitHub REST stargazers endpoint with the `star+json` media type, which includes `starred_at`.
Needs a token in GITHUB_TOKEN (in Actions the built-in token works for public repos).
Fetched timestamps are cached in data/stars-<owner>-<repo>.json and only new pages are fetched next time.

Usage
  GITHUB_TOKEN=... python3 flowstars.py            # real data, writes v1/stars/*.svg (out/stars outside the brand repo)
  python3 flowstars.py --sample                     # preview with a synthetic curve (marked "Sample data")
"""
import os, sys, json, math, argparse, datetime as dt, urllib.request, urllib.error, random
from flowbadges import text_outline, text_width, icon_svg, shape_path, PALETTE, HERE

CFG = json.load(open(os.path.join(HERE, "stars.json")))
try:                                   # brand repo layout: tools/ next to v1/
    from flowbadges import V1
    OUT = os.path.join(V1, "stars")
except ImportError:
    OUT = os.path.join(HERE, "out", "stars")
DATA = os.path.join(HERE, "data")

# series colours by project ("color" in stars.json: 0 = Flow red, 1 = Desktop blue), validated (light on surfaceContainer #ffe9e6, dark on #2f1a17): all checks pass
SERIES = {"light": ["#BC0100", "#0059BA"], "dark": ["#F2402C", "#488FFF"]}

# ---------------------------------------------------------------- data
def _get(url, token, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "Authorization": f"Bearer {token}",
                                               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "flow-brand"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        sys.exit(f"GET {url} -> {e.code}: {e.read().decode(errors='replace')[:300]}")

def _pages(repo, token, page, stamps):
    while True:
        batch = _get(f"https://api.github.com/repos/{repo}/stargazers?per_page=100&page={page}",
                     token, "application/vnd.github.star+json")
        if not batch:
            return stamps
        stamps += [b["starred_at"] for b in batch]
        if len(batch) < 100 or page >= 400:       # the API stops at 40k stargazers
            return stamps
        page += 1

_fetched = {}

def fetch_stars(repo, token):
    """Star dates for repo, oldest first. The cache holds {"hidden": n, "stamps": [...]} (timestamps only)."""
    if repo in _fetched:                          # a repo can appear in several charts
        return _fetched[repo]
    os.makedirs(DATA, exist_ok=True)
    cache = os.path.join(DATA, "stars-" + repo.replace("/", "-") + ".json")
    saved = json.load(open(cache)) if os.path.exists(cache) else {}
    stamps, hidden = saved.get("stamps", []), saved.get("hidden")
    page = len(stamps) // 100 + 1
    stamps = _pages(repo, token, page, stamps[: (page - 1) * 100])   # refetch the last partial page
    # GitHub's stargazers_count also counts stars the list never returns (e.g. from hidden accounts),
    # so a steady gap between the two is normal. An unstar shifts every later page and changes that gap;
    # when it changes, start over (a full fetch is one request per 100 stars).
    gap = min(_get(f"https://api.github.com/repos/{repo}", token)["stargazers_count"], 40000) - len(stamps)
    if hidden is not None and gap != hidden:
        print(f"{repo}: the star count moved by {gap - hidden} against the cache; refetching all pages", flush=True)
        stamps = _pages(repo, token, 1, [])
        gap = min(_get(f"https://api.github.com/repos/{repo}", token)["stargazers_count"], 40000) - len(stamps)
    json.dump({"hidden": gap, "stamps": sorted(stamps)}, open(cache, "w"))
    _fetched[repo] = sorted(dt.datetime.fromisoformat(t.replace("Z", "+00:00")).date() for t in stamps)
    return _fetched[repo]

def sample_stars(start, end, total, seed=7):
    """Synthetic but plausible curve for previews only."""
    rnd = random.Random(seed)
    days = (end - start).days
    w = []
    for d in range(days + 1):
        base = 0.4 + 2.2 / (1 + math.exp(-(d - days * 0.35) / (days * 0.08)))
        spike = 9 * math.exp(-((d - days * 0.42) / 6) ** 2) + 5 * math.exp(-((d - days * 0.71) / 5) ** 2)
        w.append(max(0.0, base + spike + rnd.uniform(-0.3, 0.3)))
    k = total / sum(w)
    out, acc = [], 0.0
    for d, x in enumerate(w):
        acc += x * k
        while len(out) < round(acc):
            out.append(start + dt.timedelta(days=d))
    return out[:total]

def cumulative(dates, start, end):
    """Daily cumulative counts from start to end inclusive."""
    counts, i, out = 0, 0, []
    d = start
    while d <= end:
        while i < len(dates) and dates[i] <= d:
            counts += 1; i += 1
        out.append((d, counts)); d += dt.timedelta(days=1)
    return out

# ---------------------------------------------------------------- helpers
def nice_step(maxv, target=5):
    raw = maxv / target
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag

def fmt(n):
    return f"{n:,}"

def short(n):
    return f"{n/1000:g}k" if n >= 1000 else str(n)

def txt(s, size, x, y, fill, wght=500, anchor="start"):
    w = text_width(s, size, wght=wght)
    if anchor == "end": x -= w
    elif anchor == "middle": x -= w / 2
    d, _ = text_outline(s, size, x, y, wght=wght)
    return f'<path fill="{fill}" d="{d}"/>', w

def month_ticks(start, end, maxn=8):
    months = []
    d = dt.date(start.year, start.month, 1)
    while d <= end:
        if d >= start: months.append(d)
        d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    step = max(1, math.ceil(len(months) / maxn))
    return months[::step]

# ---------------------------------------------------------------- render
def render(chart, series, theme, animated, sample, today):
    P = PALETTE[theme]
    W, H = 960, 460
    L, R, T, B = 76, W - 56, 150, H - 58
    body = [f'<rect width="{W}" height="{H}" rx="40" fill="{P["surfaceContainer"]}"/>']
    css = []

    # header: Flow mark, title, subtitle
    body.append(f'<path fill="#FFFFFF" d="{shape_path("cookie12", 64, 62, 24)}"/>')
    body.append(icon_svg("flow", 64, 63, 30, None))
    body.append(txt(chart["title"], 26, 102, 62, P["onSurface"], 720)[0])
    body.append(txt(chart["subtitle"], 14, 102, 84, P["onSurfaceVariant"], 500)[0])

    # hero number (total)
    total = sum(s["points"][-1][1] for s in series)
    body.append(txt(fmt(total), 44, W - 44, 72, P["onSurface"], 800, "end")[0])
    body.append(txt(chart.get("unit", "stars on GitHub"), 13.5, W - 44, 94, P["onSurfaceVariant"], 500, "end")[0])

    # legend (2+ series): swatch pill + label + count
    if len(series) > 1:
        x = 102
        for s in series:
            body.append(f'<rect x="{x}" y="108" width="22" height="10" rx="5" fill="{s["color"]}"/>')
            t, w = txt(f'{s["label"]}  {fmt(s["points"][-1][1])}', 13.5, x + 30, 118, P["onSurface"], 600)
            body.append(t); x += 30 + w + 24

    if sample:
        t, w = txt("Sample data · the real chart builds in CI", 12.5, 0, 0, P["onSurfaceVariant"], 600)
        sx = (W - w) / 2 - 14
        body.append(f'<rect x="{sx:.1f}" y="24" width="{w+28:.1f}" height="26" rx="13" fill="{P["surfaceContainerHighest"]}"/>')
        body.append(txt("Sample data · the real chart builds in CI", 12.5, W / 2, 41.5, P["onSurfaceVariant"], 600, "middle")[0])

    # scales
    start = min(s["points"][0][0] for s in series)
    end = today
    maxv = max(s["points"][-1][1] for s in series)
    step = nice_step(maxv * 1.08)
    ymax = math.ceil(maxv * 1.08 / step) * step
    span = max(1, (end - start).days)
    X = lambda d: L + (R - L) * (d - start).days / span
    Y = lambda v: B - (B - T) * v / ymax

    # grid + y labels
    v = 0
    while v <= ymax + 1e-9:
        y = Y(v)
        body.append(f'<line x1="{L}" y1="{y:.1f}" x2="{R}" y2="{y:.1f}" stroke="{P["outlineVariant"]}" '
                    f'stroke-width="1" stroke-opacity="{0.9 if v == 0 else 0.45}"/>')
        body.append(txt(short(int(v)), 12, L - 12, y + 4, P["onSurfaceVariant"], 500, "end")[0])
        v += step
    # x labels (months)
    for m in month_ticks(start, end):
        x = X(m)
        lab = m.strftime("%b") + (f" ’{m.strftime('%y')}" if m.month == 1 or m == month_ticks(start, end)[0] else "")
        body.append(txt(lab, 12, x, B + 22, P["onSurfaceVariant"], 500, "middle")[0])

    # series
    for si, s in enumerate(series):
        pts = s["points"]
        # thin to ~1 point per 2px
        stride = max(1, len(pts) // int((R - L) / 2))
        pts = pts[::stride] + ([pts[-1]] if pts[-1] not in pts[::stride] else [])
        line = "M" + "L".join(f"{X(d):.1f} {Y(c):.1f}" for d, c in pts)
        if len(series) == 1:
            gid = f"g{si}"
            body.append(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                        f'<stop offset="0" stop-color="{s["color"]}" stop-opacity="0.28"/>'
                        f'<stop offset="1" stop-color="{s["color"]}" stop-opacity="0"/></linearGradient></defs>')
            area = line + f"L{X(pts[-1][0]):.1f} {B}L{X(pts[0][0]):.1f} {B}Z"
            body.append(f'<path class="area" d="{area}" fill="url(#{gid})"/>')
        body.append(f'<path class="line" pathLength="1" d="{line}" fill="none" stroke="{s["color"]}" '
                    f'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')

        # milestones (single series): every "nice" thousand
        last = s["points"][-1][1]
        ms = next((m for m in (25, 50, 100, 250, 500, 1000, 5000, 10000) if last / m <= 5), 10000)
        if len(series) == 1 and last >= ms:
            target = ms
            for d, c in s["points"]:
                if c >= target:
                    mx, my = X(d), Y(target)
                    body.append(f'<path class="mk" fill="{P["surfaceContainer"]}" d="{shape_path("sunny", mx, my, 9)}"/>')
                    body.append(f'<path class="mk" fill="{s["color"]}" d="{shape_path("sunny", mx, my, 7)}"/>')
                    t, _ = txt(short(target), 12.5, mx - 12, my - 6, P["onSurface"], 700, "end")
                    body.append(t)
                    target += ms

        # endpoint: expressive cookie with a star, plus a direct label for multi-series
        ex, ey = X(s["points"][-1][0]), Y(s["points"][-1][1])
        body.append(f'<path class="end" fill="{P["surfaceContainer"]}" d="{shape_path("cookie9", ex, ey, 15)}"/>')
        body.append(f'<path class="end" fill="{s["color"]}" d="{shape_path("cookie9", ex, ey, 12.5)}"/>')
        body.append(f'<g class="end">{icon_svg("ms:star", ex, ey, 14, "#FFFFFF")}</g>')
        if len(series) > 1:
            body.append(txt(s["label"], 12.5, ex - 16, ey - 14, P["onSurface"], 650, "end")[0])

    if animated:
        css.append(".line{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.8s cubic-bezier(.2,0,0,1) .2s forwards}"
                   ".area,.mk{opacity:0;animation:fade .6s ease 1.4s forwards}"
                   ".end{opacity:0;animation:fade .4s ease 1.9s forwards}"
                   "@keyframes draw{to{stroke-dashoffset:0}}@keyframes fade{to{opacity:1}}"
                   "@media (prefers-reduced-motion: reduce){.line{stroke-dashoffset:0}.area,.mk,.end{opacity:1}}")

    upd = ("Updated " + today.strftime("%-d %b %Y")) if not sample else ""
    if upd:
        body.append(txt(upd, 12, W - 44, 113, P["onSurfaceVariant"], 500, "end")[0])   # under the unit, clear of the month labels

    label = f'{chart["title"]}: {fmt(total)} stars as of {today.isoformat()}' + (" (sample data)" if sample else "")
    style = ("<style>" + "".join(css) + "@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>") if css else ""
    esc = label.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{esc}"><title>{esc}</title>{style}{"".join(body)}</svg>\n')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="synthetic preview data")
    ap.add_argument("--out", default=None, help="output folder (default: v1/stars in the brand repo)")
    ap.add_argument("--only", default=None, help="render only this chart id")
    ap.add_argument("--force", action="store_true", help="re-render even if no star counts changed")
    a = ap.parse_args()
    global OUT
    OUT = a.out or OUT
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not a.sample and not token:
        sys.exit("Set GITHUB_TOKEN (or run with --sample for a preview).")
    today = dt.date.today()
    os.makedirs(OUT, exist_ok=True)
    for chart in CFG["charts"]:
        if a.only and chart["id"] != a.only:
            continue
        series = []
        for i, r in enumerate(chart["repos"]):
            if a.sample:
                dates = sample_stars(dt.date.fromisoformat(r["sample_start"]), today, r["sample_total"], seed=7 + i)
            else:
                dates = fetch_stars(r["repo"], token)
            if not dates:
                continue
            series.append({"label": r["label"], "points": cumulative(dates, dates[0], today), "ci": r.get("color", i)})
        # skip charts whose totals haven't changed, so the daily job doesn't commit a new "Updated" date every day
        state_file = os.path.join(DATA, "stars-state.json")
        state = json.load(open(state_file)) if os.path.exists(state_file) else {}
        totals = {s["label"]: s["points"][-1][1] for s in series}
        exists = os.path.exists(os.path.join(OUT, f'{chart["id"]}-light.svg'))
        if not a.sample and not a.force and exists and state.get(chart["id"]) == totals:
            print(f'{chart["id"]}: unchanged {totals}')
            continue
        if not a.sample:
            state[chart["id"]] = totals
            os.makedirs(DATA, exist_ok=True)
            json.dump(state, open(state_file, "w"), indent=1, sort_keys=True)
        print(f'{chart["id"]}: {totals}')
        for theme in ("light", "dark"):
            for s in series:
                s["color"] = SERIES[theme][s["ci"] % 2]
            for anim in (False, True):
                svg = render(chart, series, theme, anim, a.sample, today)
                open(os.path.join(OUT, f'{chart["id"]}-{theme}{"-animated" if anim else ""}.svg'), "w").write(svg)
    print("wrote star charts to", OUT)

if __name__ == "__main__":
    main()
