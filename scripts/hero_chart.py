"""Build the home page's pitch-movement chart as inline SVG.

    python3 scripts/hero_chart.py data/hero-movement.csv > _hero-chart.qmd

The CSV has one row per pitch: pt (Statcast pitch code), hb, ivb (inches), the
same columns the Pitcher Arsenal app plots. Colors and axes match the app's
Movement tab, so the chart reads the same on both. Export a new pitcher's CSV
from the app repo with:

    Rscript -e 'invisible(lapply(sort(list.files("R", full.names=TRUE)), source));
      d <- readRDS("data/app_data.rds"); p <- reconcile_pitch_codes(d[d$pitcher == ID, ]);
      write.csv(data.frame(pt=p$pitch_type, hb=round(p$hb,1), ivb=round(p$ivb,1)),
                "hero-movement.csv", row.names=FALSE)'
"""
import csv
import sys
from collections import defaultdict

# The app's colors (R/theme.R pitch_colors) and Savant's names.
COLORS = {"FF": "#FF0000", "SI": "#FFA500", "CU": "#8B008B", "CH": "#228B22",
          "SL": "#FFFF00", "FS": "#00CED1", "FC": "#8B4513", "ST": "#DDB100",
          "KC": "#6A0DAD", "SV": "#7CFC00", "KN": "#808080"}
NAMES = {"FF": "Four-seam", "SI": "Sinker", "CU": "Curveball", "CH": "Changeup",
         "SL": "Slider", "FS": "Splitter", "FC": "Cutter", "ST": "Sweeper",
         "KC": "Knuckle curve", "SV": "Slurve", "KN": "Knuckleball"}

W, H = 560, 470
L, R, T, B = 52, 18, 16, 50          # plot margins
LIM = 25                              # inches, both axes, as in the app


def x(v): return L + (v + LIM) / (2 * LIM) * (W - L - R)
def y(v): return T + (LIM - v) / (2 * LIM) * (H - T - B)


def main(path):
    rows = [(r["pt"], float(r["hb"]), float(r["ivb"])) for r in csv.DictReader(open(path))]
    by = defaultdict(list)
    for pt, hb, ivb in rows:
        by[pt].append((hb, ivb))
    order = sorted(by, key=lambda k: -len(by[k]))
    n = len(rows)

    out = []
    a = out.append
    a(f'<svg class="hero-chart" viewBox="0 0 {W} {H}" role="img" '
      f'aria-labelledby="hero-chart-title hero-chart-desc">')
    a('<title id="hero-chart-title">Pitch movement chart</title>')
    desc = ", ".join(f"{NAMES.get(k, k)} {100 * len(by[k]) / n:.0f}%" for k in order)
    a(f'<desc id="hero-chart-desc">{n:,} pitches plotted by horizontal and induced vertical '
      f'break. Pitch mix: {desc}.</desc>')

    # Grid every 10 inches, zero lines stronger.
    a('<g class="grid">')
    for v in range(-20, 21, 10):
        cls = "zero" if v == 0 else ""
        a(f'<line class="{cls}" x1="{x(v):.1f}" y1="{T}" x2="{x(v):.1f}" y2="{H - B}"/>')
        a(f'<line class="{cls}" x1="{L}" y1="{y(v):.1f}" x2="{W - R}" y2="{y(v):.1f}"/>')
        a(f'<text class="tick" x="{x(v):.1f}" y="{H - B + 16}" text-anchor="middle">{v}</text>')
        a(f'<text class="tick" x="{L - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    a('</g>')
    a(f'<text class="axis" x="{(L + W - R) / 2:.0f}" y="{H - 10}" text-anchor="middle">'
      'Horizontal break (in)</text>')
    a(f'<text class="axis" transform="translate(14 {(T + H - B) / 2:.0f}) rotate(-90)" '
      'text-anchor="middle">Induced vertical break (in)</text>')

    # Every pitch, one group per type so the reveal can stagger by type.
    for i, k in enumerate(order):
        a(f'<g class="pitches" style="--i:{i}" fill="{COLORS.get(k, "#808080")}">')
        for hb, ivb in by[k]:
            if abs(hb) <= LIM and abs(ivb) <= LIM:
                a(f'<circle cx="{x(hb):.1f}" cy="{y(ivb):.1f}" r="2.4"/>')
        a('</g>')

    # Each type's average, labelled: the labels are the legend.
    means = []
    for k in order:
        pts = by[k]
        mh = sum(p[0] for p in pts) / len(pts)
        mv = sum(p[1] for p in pts) / len(pts)
        means.append([k, x(mh), y(mv), y(mv) + 4, len(pts)])
    # Two averages close together (a sinker and a changeup often are) would
    # print their labels on top of each other. Walk the labels top to bottom
    # and push any that sits within 16 px of one above it, in the same column.
    means.sort(key=lambda m: m[3])
    for i, m in enumerate(means):
        for prev in means[:i]:
            if abs(prev[1] - m[1]) < 90 and m[3] - prev[3] < 16:
                m[3] = prev[3] + 16
    a('<g class="means">')
    for k, cx, cy, ly, cnt in means:
        a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="{COLORS.get(k, "#808080")}"/>')
        a(f'<text x="{cx + 11:.1f}" y="{ly:.1f}">{NAMES.get(k, k)} '
          f'<tspan class="pct">{100 * cnt / n:.0f}%</tspan></text>')
    a('</g>')
    a('</svg>')

    print("```{=html}")
    print("\n".join(out))
    print("```")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
