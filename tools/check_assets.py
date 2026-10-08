#!/usr/bin/env python3
"""Guardrails for v1/. Exits non-zero and lists every problem it finds.

  python3 check_assets.py --base <git ref>   # also enforce the URL contract against that commit
  python3 check_assets.py --base <ref> --contract-only   # only the URL contract (CI runs this on the
                                                         # committed tree, before regenerating)

Checks
  * URL contract: every path under v1/ in --base still exists (files are never removed or renamed)
  * every SVG is well-formed, has role="img" and a <title>, and loads nothing external
  * every -light file has a -dark twin and vice versa
  * size limits: badges and icons 40 KB, banners 80 KB
  * v1/manifest.json matches the files on disk
"""
import argparse, os, re, subprocess, sys
import xml.etree.ElementTree as ET
from make_manifest import V1, MANIFEST, render

REPO = os.path.dirname(V1)
SVG_NS = "{http://www.w3.org/2000/svg}"
LIMITS = {"badges/": 40 * 1024, "icons/": 40 * 1024, "banners/": 80 * 1024}
EXTERNAL = [
    re.compile(r"""(?:xlink:)?href\s*=\s*["']\s*(?:https?:)?//""", re.I),
    re.compile(r"""url\(\s*["']?\s*(?:https?:)?//""", re.I),
    re.compile(r"""@import""", re.I),
]
PAIR = re.compile(r"^(.*)-(light|dark)((?:-animated)?(?:-\d+)?\.\w+)$")

def files_now():
    out = set()
    for root, _, names in os.walk(V1):
        for n in names:
            if n != ".DS_Store":
                out.add(os.path.relpath(os.path.join(root, n), REPO).replace(os.sep, "/"))
    return out

def files_at(ref):
    r = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", ref, "--", "v1/"],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"cannot list v1/ at {ref}: {r.stderr.strip()}")
    return set(filter(None, r.stdout.splitlines()))

def check_svg(rel, text):
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return [f"{rel}: not well-formed XML ({e})"]
    errs = []
    if root.tag != SVG_NS + "svg":
        errs.append(f"{rel}: root element is not <svg>")
    if root.get("role") != "img":
        errs.append(f'{rel}: missing role="img"')
    title = root.find(SVG_NS + "title")
    if title is None or not (title.text or "").strip():
        errs.append(f"{rel}: missing <title>")
    for pat in EXTERNAL:
        if m := pat.search(text):
            errs.append(f"{rel}: references an external resource ({m.group(0)!r})")
    return errs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="git ref whose v1/ paths must all still exist")
    ap.add_argument("--contract-only", action="store_true", help="skip everything but the --base check")
    a = ap.parse_args()
    now, errs = files_now(), []

    if a.base:
        gone = sorted(files_at(a.base) - now)
        errs += [f"{p}: removed or renamed, but v1/ paths are a public contract (put the new look in v2/)" for p in gone]

    for rel in sorted(now) if not a.contract_only else ():
        path = os.path.join(REPO, rel)
        sub = rel[len("v1/"):]
        if rel.endswith(".svg"):
            errs += check_svg(rel, open(path, encoding="utf-8").read())
        if m := PAIR.match(os.path.basename(rel)):
            twin = f"{m[1]}-{'dark' if m[2] == 'light' else 'light'}{m[3]}"
            if f"{os.path.dirname(rel)}/{twin}" not in now:
                errs.append(f"{rel}: no matching {twin}")
        for prefix, limit in LIMITS.items():
            size = os.path.getsize(path)
            if sub.startswith(prefix) and size > limit:
                errs.append(f"{rel}: {size} bytes, over the {limit // 1024} KB limit")

    if a.contract_only:
        pass                              # the manifest may lag a config-only PR until CI regenerates
    elif not os.path.exists(MANIFEST):
        errs.append("v1/manifest.json: missing (run tools/make_manifest.py)")
    else:
        try:
            if open(MANIFEST, encoding="utf-8").read() != render():
                errs.append("v1/manifest.json: out of date (run tools/make_manifest.py)")
        except ET.ParseError:
            errs.append("v1/manifest.json: cannot be rebuilt until the broken SVGs above are fixed")

    for e in errs:
        print("::error::" + e if os.environ.get("GITHUB_ACTIONS") else "ERROR " + e)
    print(f"checked {len(now)} files under v1/: {len(errs)} problem(s)")
    sys.exit(1 if errs else 0)

if __name__ == "__main__":
    main()
