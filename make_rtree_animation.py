"""Generate an animated GIF that explains, step by step, how the STR R-tree is
built and how the incremental k-NN search walks it.

The animation uses a small random sample of the real Beijing_restaurants.txt
dataset so the bounding rectangles stay readable.

Run:
    python make_rtree_animation.py

Output:
    rtree_demo.gif
"""

import math
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.animation import FuncAnimation, PillowWriter

DATASET = "Beijing_restaurants.txt"
SAMPLE_SIZE = 240
LEAF_CAP = 10          # points per leaf (visualization only)
PARENT_CAP = 6         # leaves per parent node (visualization only)
K = 4                  # neighbors to find in the demo
SEED = 7


def read_sample(filename, sample_size, seed):
    with open(filename, "r") as f:
        f.readline()  # first line = number of records
        pts = []
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            lat, lon = float(parts[0]), float(parts[1])
            pts.append((lon, lat))  # x = lon, y = lat
    rng = random.Random(seed)
    if len(pts) > sample_size:
        pts = rng.sample(pts, sample_size)
    return pts


def mbr_of(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def build_str(points, leaf_cap, parent_cap):
    n = leaf_cap
    P = math.ceil(len(points) / n)
    S = math.ceil(math.sqrt(P))
    slice_size = S * n

    by_x = sorted(points, key=lambda p: p[0])
    slices = [by_x[i:i + slice_size] for i in range(0, len(by_x), slice_size)]

    leaves = []
    for sl in slices:
        sl_sorted = sorted(sl, key=lambda p: p[1])
        for i in range(0, len(sl_sorted), n):
            leaves.append(sl_sorted[i:i + n])

    parents = [leaves[i:i + parent_cap] for i in range(0, len(leaves), parent_cap)]
    return leaves, parents


def rect_from_mbr(mbr, pad=0.0, **kw):
    minx, miny, maxx, maxy = mbr
    return Rectangle(
        (minx - pad, miny - pad),
        (maxx - minx) + 2 * pad,
        (maxy - miny) + 2 * pad,
        fill=False,
        **kw,
    )


def mbr_intersects_circle(mbr, q, r):
    minx, miny, maxx, maxy = mbr
    dx = max(minx - q[0], 0, q[0] - maxx)
    dy = max(miny - q[1], 0, q[1] - maxy)
    return math.hypot(dx, dy) <= r


def main():
    points = read_sample(DATASET, SAMPLE_SIZE, SEED)
    leaves, parents = build_str(points, LEAF_CAP, PARENT_CAP)
    leaf_mbrs = [mbr_of(l) for l in leaves]
    parent_mbrs = [mbr_of([p for leaf in grp for p in leaf]) for grp in parents]
    root_mbr = mbr_of(points)

    # Query point near the centre of the map.
    minx, miny, maxx, maxy = root_mbr
    q = ((minx + maxx) / 2, (miny + maxy) / 2)

    # k nearest neighbours (ground truth) ordered by distance.
    ranked = sorted(points, key=lambda p: math.hypot(p[0] - q[0], p[1] - q[1]))
    knn = ranked[:K]
    kth_dist = math.hypot(knn[-1][0] - q[0], knn[-1][1] - q[1])

    # ---- Build a timeline of phases ------------------------------------
    # Each entry: (phase_name, number_of_frames)
    phases = [
        ("points", 8),
        ("leaves", len(leaf_mbrs) + 4),
        ("parents", len(parent_mbrs) + 4),
        ("root", 6),
        ("query", 6),
        ("search", 26),
        ("result", 12),
    ]
    frame_map = []  # global frame -> (phase, local_index)
    for name, count in phases:
        for i in range(count):
            frame_map.append((name, i))
    total_frames = len(frame_map)

    pad_x = (maxx - minx) * 0.05
    pad_y = (maxy - miny) * 0.05

    fig, ax = plt.subplots(figsize=(7, 7))

    def setup_axes(title, subtitle=""):
        ax.clear()
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=14, fontweight="bold")
        if subtitle:
            ax.text(0.5, -0.04, subtitle, transform=ax.transAxes,
                    ha="center", va="top", fontsize=10, color="#444")

    def draw_points(color="#888", size=10, alpha=0.8):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.scatter(xs, ys, s=size, c=color, alpha=alpha, zorder=2)

    def update(frame):
        phase, i = frame_map[frame]

        if phase == "points":
            setup_axes("1. The data: restaurant locations",
                       "Each dot is one restaurant (a 2D point).")
            draw_points()

        elif phase == "leaves":
            setup_axes("2. Group nearby points into LEAVES",
                       "STR sorts by x, slices, sorts by y -> tight leaf boxes (MBRs).")
            draw_points()
            shown = min(i, len(leaf_mbrs))
            for m in leaf_mbrs[:shown]:
                ax.add_patch(rect_from_mbr(m, edgecolor="#2e7d32", lw=1.6, zorder=3))

        elif phase == "parents":
            setup_axes("3. Group leaves into PARENT nodes",
                       "Parent MBRs wrap several leaf MBRs (boxes inside boxes).")
            draw_points()
            for m in leaf_mbrs:
                ax.add_patch(rect_from_mbr(m, edgecolor="#a5d6a7", lw=1.0, zorder=3))
            shown = min(i, len(parent_mbrs))
            for m in parent_mbrs[:shown]:
                ax.add_patch(rect_from_mbr(m, edgecolor="#1565c0", lw=2.0, zorder=4))

        elif phase == "root":
            setup_axes("4. The ROOT wraps everything",
                       "Top of the tree = one MBR covering all points.")
            draw_points()
            for m in leaf_mbrs:
                ax.add_patch(rect_from_mbr(m, edgecolor="#a5d6a7", lw=0.8, zorder=3))
            for m in parent_mbrs:
                ax.add_patch(rect_from_mbr(m, edgecolor="#90caf9", lw=1.2, zorder=4))
            ax.add_patch(rect_from_mbr(root_mbr, edgecolor="#6a1b9a", lw=2.6,
                                       linestyle="--", zorder=5))

        elif phase == "query":
            setup_axes("5. A query point q arrives",
                       "We want the k nearest restaurants to q.")
            draw_points(alpha=0.5)
            for m in parent_mbrs:
                ax.add_patch(rect_from_mbr(m, edgecolor="#cccccc", lw=1.0, zorder=3))
            ax.scatter([q[0]], [q[1]], s=160, marker="*", c="#d81b60",
                       edgecolor="black", zorder=6, label="query q")
            ax.legend(loc="upper right")

        elif phase == "search":
            setup_axes("6. Incremental k-NN search",
                       "Grow a search radius; expand only boxes it touches, prune the rest.")
            draw_points(alpha=0.4)
            frac = (i + 1) / phases_count("search")
            r = kth_dist * 1.25 * frac
            # Highlight which leaf MBRs the search must visit vs prune.
            for m in leaf_mbrs:
                if mbr_intersects_circle(m, q, r):
                    ax.add_patch(rect_from_mbr(m, edgecolor="#ef6c00", lw=1.8, zorder=3))
                else:
                    ax.add_patch(rect_from_mbr(m, edgecolor="#dddddd", lw=0.8, zorder=3))
            ax.add_patch(Circle(q, r, fill=False, edgecolor="#d81b60",
                                lw=1.8, linestyle="--", zorder=5))
            # Mark neighbours already inside the radius.
            inside = [p for p in knn
                      if math.hypot(p[0] - q[0], p[1] - q[1]) <= r]
            if inside:
                ax.scatter([p[0] for p in inside], [p[1] for p in inside],
                           s=70, c="#fdd835", edgecolor="black", zorder=6)
            ax.scatter([q[0]], [q[1]], s=160, marker="*", c="#d81b60",
                       edgecolor="black", zorder=7)

        elif phase == "result":
            setup_axes(f"7. Done: the {K} nearest neighbours",
                       "Neighbours are returned one-by-one, closest first.")
            draw_points(alpha=0.35)
            ax.add_patch(Circle(q, kth_dist, fill=False, edgecolor="#d81b60",
                                lw=1.6, linestyle="--", zorder=5))
            for rank, p in enumerate(knn, start=1):
                ax.scatter([p[0]], [p[1]], s=110, c="#fdd835",
                           edgecolor="black", zorder=6)
                ax.annotate(str(rank), (p[0], p[1]), textcoords="offset points",
                            xytext=(6, 6), fontsize=10, fontweight="bold")
            ax.scatter([q[0]], [q[1]], s=180, marker="*", c="#d81b60",
                       edgecolor="black", zorder=7)

        return []

    def phases_count(name):
        for n, c in phases:
            if n == name:
                return c
        return 1

    anim = FuncAnimation(fig, update, frames=total_frames, interval=350, blit=False)
    writer = PillowWriter(fps=4)
    anim.save("rtree_demo.gif", writer=writer, dpi=90)
    print(f"Saved rtree_demo.gif ({total_frames} frames)")


if __name__ == "__main__":
    main()
