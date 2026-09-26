"""Geometry of the brain-drain logo (docs/img/logo.svg) as plain numbers, shared by the board silkscreen
(hardware/tools/branding.py) and the lid engraving (enclosure/tools/gen_logo.py). Units are the SVG's pixels, y down.

    from logo_geom import load; g = load()   # g.tentacles, g.gyri, g.brain, g.eyes, g.hdds, g.bbox
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SVG = Path(__file__).resolve().parents[2] / "docs" / "img" / "logo.svg"
NUM = r"(-?\d+(?:\.\d+)?)"


def bez(p, n=28):
    """Sample a cubic Bezier given as 4 (x, y) points."""
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3 * p[0][0] + 3 * u * u * t * p[1][0] + 3 * u * t * t * p[2][0] + t**3 * p[3][0],
                    u**3 * p[0][1] + 3 * u * u * t * p[1][1] + 3 * u * t * t * p[2][1] + t**3 * p[3][1]))
    return out


@dataclass
class Logo:
    tentacles: list = field(default_factory=list)   # polylines, stroke width 34 px
    gyri: list = field(default_factory=list)        # polylines (fissure first), stroke 9-10 px
    brain: tuple = (600, 290, 215, 175)              # cx, cy, rx, ry
    eyes: list = field(default_factory=list)         # (cx, cy, rx, ry, pupil_cx, pupil_cy, pupil_r)
    hdds: list = field(default_factory=list)         # (x, y) top-left of each 92 x 60 drive icon
    tentacle_w: float = 34.0
    gyri_w: float = 9.0
    bbox: tuple = (0, 0, 0, 0)


def load(path: Path = SVG) -> Logo:
    s = path.read_text()
    g = Logo()
    path_re = re.compile(r'<path d="M' + NUM + "," + NUM + r" C" + NUM + "," + NUM + " " + NUM + "," + NUM + " " + NUM + "," + NUM + r'"([^>]*)/>')
    for m in path_re.finditer(s):
        v = [float(x) for x in m.groups()[:8]]
        attrs = m.group(9)
        pts = bez([(v[0], v[1]), (v[2], v[3]), (v[4], v[5]), (v[6], v[7])])
        if 'stroke="url(#tent)"' in attrs:
            g.tentacles.append(pts)
        elif 'stroke="#8d3a55"' in attrs:
            g.gyri.append(pts)
    for m in re.finditer(r'<ellipse cx="' + NUM + '" cy="' + NUM + '" rx="' + NUM + '" ry="' + NUM + r'" fill="#fff6f8"', s):
        cx, cy, rx, ry = (float(x) for x in m.groups())
        g.eyes.append((cx, cy, rx, ry, cx + 6, cy + 6, 16.0))
    g.hdds = [(float(a), float(b)) for a, b in re.findall(r'<g transform="translate\(' + NUM + "," + NUM + r'\)"', s)]
    xs = [p[0] for t in g.tentacles for p in t] + [h[0] + p for h in g.hdds for p in (0, 92)]
    ys = [p[1] for t in g.tentacles for p in t] + [h[1] + p for h in g.hdds for p in (0, 60)] + [290 - 175]
    g.bbox = (min(xs), min(ys), max(xs), max(ys))
    return g


if __name__ == "__main__":
    lg = load()
    print(len(lg.tentacles), "tentacles,", len(lg.gyri), "brain lines,", len(lg.eyes), "eyes,", len(lg.hdds), "drives, bbox", lg.bbox)
