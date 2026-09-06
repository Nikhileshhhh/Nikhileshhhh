#!/usr/bin/env python3
"""Generate assets/github.svg — a self-hosted, animated GitHub activity panel.

Runs in CI against the live GitHub API. If the API is unreachable it exits
without touching the existing SVG, so a bad API day never blanks the README.
A --snapshot file can be supplied to render offline from cached metadata.
"""
import json, os, sys, datetime, argparse, urllib.request, urllib.error

USER = os.environ.get("GITHUB_USER", "Nikhileshhhh")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "github.svg")

# GitHub linguist colours
LANG_COLOR = {
    "Python": "#4DA6FF", "TypeScript": "#2F5FD0", "JavaScript": "#F1E05A",
    "Java": "#B07219", "Dart": "#00B4AB", "Jupyter Notebook": "#DA5B0B",
    "HTML": "#E34C26", "CSS": "#563D7C", "C#": "#178600", "Shell": "#89E051",
}
OTHER = "#41556d"


def fetch():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-panel"},
    )
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        repos = json.load(r)
    return [
        {"name": x["name"], "language": x.get("language"),
         "stars": x.get("stargazers_count", 0), "created_at": x["created_at"],
         "fork": x.get("fork", False)}
        for x in repos if not x.get("fork")
    ]


def month_index(iso, base):
    d = datetime.datetime.strptime(iso[:7], "%Y-%m")
    return (d.year - base.year) * 12 + (d.month - base.month)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(repos):
    repos = sorted(repos, key=lambda r: r["created_at"])
    total = len(repos)
    stars = sum(r["stars"] for r in repos)
    langs = [r["language"] for r in repos if r["language"]]
    n_lang = len(set(langs))

    base = datetime.datetime.strptime(repos[0]["created_at"][:7], "%Y-%m")
    last = datetime.datetime.strptime(repos[-1]["created_at"][:7], "%Y-%m")
    span = (last.year - base.year) * 12 + (last.month - base.month)
    months = max(span, 1)

    W, H = 940, 360
    X0, X1 = 62, 878
    step = (X1 - X0) / months

    # ── language distribution by primary language ──
    counts = {}
    for r in repos:
        counts[r["language"] or "Other"] = counts.get(r["language"] or "Other", 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (kv[0] == "Other", -kv[1], kv[0]))

    p = []
    p.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub activity: {total} public repositories across {n_lang} languages">
<defs>
  <linearGradient id="gPanel" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#0d1a26"/>
  </linearGradient>
  <filter id="gGlow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="3.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <style>
    .mono {{ font-family: ui-monospace, 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace; }}
    .sans {{ font-family: 'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif; }}
  </style>
</defs>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="url(#gPanel)" stroke="#1e3350"/>
<text class="sans" x="26" y="34" font-size="17" font-weight="700" fill="#E6EDF3">GitHub activity</text>
<text class="mono" x="150" y="34" font-size="12" fill="#5C7A99">/ generated in this repo, refreshed daily</text>
<g transform="translate(788 20)">
  <rect width="130" height="22" rx="11" fill="#0c1a17" stroke="#22D3A6" stroke-opacity="0.45"/>
  <circle cx="14" cy="11" r="3.6" fill="#22D3A6"><animate attributeName="opacity" values="1;0.2;1" dur="1.8s" repeatCount="indefinite"/></circle>
  <text class="mono" x="26" y="15" font-size="10.5" fill="#8CE8CF" letter-spacing="1">SELF-HOSTED</text>
</g>
<line x1="20" y1="50" x2="{W-20}" y2="50" stroke="#1b2a3e"/>''')

    # ── KPI tiles ──
    since = base.strftime("%b %Y")
    kpis = [
        ("PUBLIC REPOS", str(total), "#00E5FF"),
        ("LANGUAGES", str(n_lang), "#A855F7"),
        ("BUILDING SINCE", since, "#22D3A6"),
        ("STARS EARNED", str(stars), "#FBBF24"),
    ]
    tw, gap = 205, 14
    for i, (label, val, col) in enumerate(kpis):
        x = 26 + i * (tw + gap)
        fs = 30 if len(val) <= 4 else 21
        p.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" begin="{0.15*i:.2f}s" fill="freeze"/>
  <rect x="{x}" y="66" width="{tw}" height="72" rx="12" fill="#0f1b2d" stroke="{col}" stroke-opacity="0.35"/>
  <rect x="{x}" y="66" width="3" height="72" rx="1.5" fill="{col}"/>
  <text class="mono" x="{x+18}" y="90" font-size="9.5" fill="#5C7A99" letter-spacing="1.6">{label}</text>
  <text class="sans" x="{x+18}" y="124" font-size="{fs}" font-weight="800" fill="{col}" filter="url(#gGlow)">{val}</text>
</g>''')

    # ── timeline ──
    p.append(f'<text class="mono" x="26" y="172" font-size="9.5" fill="#41556d" letter-spacing="1.8">REPOSITORY TIMELINE</text>')
    p.append(f'<line x1="{X0}" y1="252" x2="{X1}" y2="252" stroke="#2c4a68"/>')
    p.append(f'<rect x="{X0}" y="251" height="2" fill="#00E5FF" width="0" filter="url(#gGlow)">'
             f'<animate attributeName="width" from="0" to="{X1-X0}" begin="0.4s" dur="2.2s" fill="freeze"/></rect>')

    # month ticks (every 3 months)
    for m in range(0, months + 1, 3):
        x = X0 + m * step
        d = base + datetime.timedelta(days=31 * m)
        d = datetime.datetime(base.year + (base.month - 1 + m) // 12, (base.month - 1 + m) % 12 + 1, 1)
        p.append(f'<line x1="{x:.1f}" y1="252" x2="{x:.1f}" y2="258" stroke="#2c4a68"/>')
        p.append(f'<text class="mono" x="{x:.1f}" y="272" font-size="9" fill="#41556d" text-anchor="middle">{d.strftime("%b %y")}</text>')

    stack = {}
    for i, r in enumerate(repos):
        mi = month_index(r["created_at"], base)
        k = stack.get(mi, 0); stack[mi] = k + 1
        x = X0 + mi * step
        y = 240 - k * 15
        col = LANG_COLOR.get(r["language"], OTHER)
        begin = 0.5 + i * 0.11
        p.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.35s" begin="{begin:.2f}s" fill="freeze"/>
  <line x1="{x:.1f}" y1="{y+6}" x2="{x:.1f}" y2="252" stroke="{col}" stroke-opacity="0.35"/>
  <circle cx="{x:.1f}" cy="{y}" r="0" fill="{col}"><animate attributeName="r" from="0" to="5" begin="{begin:.2f}s" dur="0.4s" fill="freeze"/></circle>
</g>''')

    # ── language bar ──
    p.append(f'<text class="mono" x="26" y="300" font-size="9.5" fill="#41556d" letter-spacing="1.8">BY PRIMARY LANGUAGE</text>')
    bx, bw = 26, W - 52
    cx = bx
    for i, (lang, cnt) in enumerate(ordered):
        seg = bw * cnt / total
        col = LANG_COLOR.get(lang, OTHER)
        vis = max(seg - 3, 2)
        p.append(f'<rect x="{cx:.1f}" y="310" width="0" height="10" rx="2" fill="{col}">'
                 f'<animate attributeName="width" from="0" to="{vis:.1f}" begin="{1.2+0.12*i:.2f}s" dur="0.6s" fill="freeze"/></rect>')
        cx += seg
    lx = 26
    for i, (lang, cnt) in enumerate(ordered):
        p.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.4s" begin="{1.6+0.1*i:.2f}s" fill="freeze"/>
  <circle cx="{lx+4}" cy="{340}" r="4" fill="{LANG_COLOR.get(lang, OTHER)}"/>
  <text class="mono" x="{lx+14}" y="344" font-size="10" fill="#8B97A8">{esc(lang)} {cnt}</text>
</g>''')
        lx += 22 + len(lang) * 6.1 + len(str(cnt)) * 6.1
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", help="render from a cached JSON list instead of the API")
    a = ap.parse_args()
    try:
        repos = json.load(open(a.snapshot)) if a.snapshot else fetch()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        print(f"GitHub API unreachable ({e}); leaving {OUT} untouched", file=sys.stderr)
        sys.exit(0)
    if not repos:
        print("no repositories returned; leaving existing SVG", file=sys.stderr)
        sys.exit(0)
    open(OUT, "w").write(render(repos))
    print(f"wrote {OUT} from {len(repos)} repositories")
