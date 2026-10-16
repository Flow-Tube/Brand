#!/usr/bin/env python3
"""Refreshes the live numbers on the release, download and Open Collective backer chips.

For each repo below it reads every release from the GitHub API, then:
  * release   = newest stable tag (prereleases and drafts are skipped)
  * downloads = sum of download_count over all release assets, rounded down: 950, 4.8k+, 48k+, 1.2M+
  * backers   = backersCount from Open Collective's public JSON: "Be the first", "1 backer", "<n> backers",
                "1.2k backers" (rounded down). If Open Collective is unreachable the chip keeps its value.
Balance and income are never shown.
The values are saved into badges.json (so a full rebuild keeps them) and only those chips are re-rendered.

  GITHUB_TOKEN=... python3 update_stats.py
"""
import json, os, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "badges.json")
REPOS = {  # repo -> (release chip id, downloads chip id)
    "Flow-Tube/Flow": ("release", "downloads"),
    "Flow-Tube/Flow-Desktop": ("desktop-release", "desktop-downloads"),
}
OPENCOLLECTIVE = ("flow-tube", "opencollective")   # collective slug, backers chip id

def releases(repo):
    out, page = [], 1
    while True:
        req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}",
                                     headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        if os.environ.get("GITHUB_TOKEN"):
            req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
        batch = json.load(urllib.request.urlopen(req, timeout=30))
        out += batch
        if len(batch) < 100:
            return out
        page += 1

def compact(n):
    """Round down, so the badge never claims more than is true."""
    for unit, size in (("M", 1_000_000), ("k", 1_000)):
        if n >= size:
            whole = n // size
            if whole < 10:
                tenths = n * 10 // size
                return f"{tenths // 10}.{tenths % 10}{unit}+" if tenths % 10 else f"{whole}{unit}+"
            return f"{whole}{unit}+"
    return str(n)

def backers_label(n):
    if n == 0:
        return "Be the first"
    if n == 1:
        return "1 backer"
    return f"{n} backers" if n < 1000 else compact(n).rstrip("+") + " backers"

def backers(slug):
    """backersCount from Open Collective, or None (with a warning) if it can't be read. Never raises."""
    try:
        req = urllib.request.Request(f"https://opencollective.com/{slug}.json",
                                     headers={"Accept": "application/json", "User-Agent": "flow-brand-stats"})
        n = json.load(urllib.request.urlopen(req, timeout=15)).get("backersCount")
        if isinstance(n, int) and not isinstance(n, bool) and n >= 0:
            return n
        problem = f"no usable backersCount ({n!r})"
    except Exception as e:                        # network, HTTP, timeout, bad JSON: all harmless here
        problem = f"{type(e).__name__}: {e}"
    print(f"::warning::Open Collective {slug}: {problem}; keeping the current backers chip", flush=True)
    return None

def stats(repo):
    rel = releases(repo)
    stable = [r for r in rel if not r["draft"] and not r["prerelease"]]
    latest = max(stable, key=lambda r: r["published_at"] or r["created_at"])["tag_name"] if stable else None
    total = sum(a["download_count"] for r in rel for a in r["assets"])
    return latest, total

def main():
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    chips = {b["id"]: b for b in cfg["split"]}
    values = {}
    for repo, (rel_id, dl_id) in REPOS.items():
        latest, total = stats(repo)
        print(f"{repo}: latest stable {latest}, {total} downloads -> {compact(total)}", flush=True)
        if latest:
            values[rel_id] = latest
        values[dl_id] = compact(total)
    slug, chip = OPENCOLLECTIVE
    n = backers(slug)
    if n is not None:
        print(f"Open Collective {slug}: {n} backers -> {backers_label(n)}", flush=True)
        values[chip] = backers_label(n)
    missing = [i for i in values if i not in chips]
    if missing:
        sys.exit(f"badges.json has no split chip for: {', '.join(missing)}")
    for i, v in values.items():
        chips[i]["value"] = v
    with open(CONFIG, "w", encoding="utf-8") as f:
        f.write(json.dumps(cfg, indent=1, ensure_ascii=False))
    args = [sys.executable, os.path.join(HERE, "flowbadges.py"), "--only", ",".join(values)]
    for i, v in values.items():
        args += ["--set", f"{i}={v}"]
    subprocess.run(args, check=True)
    subprocess.run([sys.executable, os.path.join(HERE, "make_manifest.py")], check=True)

if __name__ == "__main__":
    main()
