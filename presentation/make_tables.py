"""Draws every table of the deck as a plain image (no fills, thin rules) from tables_spec.json."""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

plt.rcParams["font.family"] = "STIXGeneral"
import random
random.seed(7)
INK, RULE = "k", "#888888"
PAD_X, PAD_Y = 0.06, 0.045  # inches


def wrap(fig, text, fs, width, bold):
    """Greedy word wrap so that each line fits in width (inches)."""
    r = fig.canvas.get_renderer()
    t = fig.text(0, 0, "", fontsize=fs, fontweight="bold" if bold else "normal")
    lines = []
    for para in str(text).split("\n"):
        cur = ""
        for word in para.split():
            trial = (cur + " " + word).strip()
            t.set_text(trial)
            if t.get_window_extent(r).width / fig.dpi <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    t.remove()
    return lines


def render(spec):
    w = spec["w"]
    tot = sum(spec["colW"])
    cw = [c * w / tot for c in spec["colW"]]
    xs = [sum(cw[:i]) for i in range(len(cw))]
    fs = spec["fs"]
    fs = fs + 1.5
    line_h = fs * 1.2 / 72
    fig = plt.figure(figsize=(w, 10), dpi=100)
    hl = set(spec["hl"])
    rows = [[(c, True, False) for c in spec["head"]]]
    for i, r in enumerate(spec["rows"]):
        rows.append([(c, False, f"{i},{j}" in hl or f"{i},{j}" in spec["colors"]) for j, c in enumerate(r)])
    laid = []
    for r in rows:
        cells = [wrap(fig, c[0], fs, cw[j] - 2 * PAD_X, c[1]) for j, c in enumerate(r)]
        h = max(max(len(c) for c in cells) * line_h + 2 * PAD_Y, spec["rowH"])
        laid.append((cells, h))
    total = sum(h for _, h in laid) + 0.04
    plt.close(fig)
    fig = plt.figure(figsize=(w, total * 1.06), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(total * 1.06, 0); ax.axis("off")
    y = 0.02
    j_ = lambda m: random.uniform(-m, m)
    ax.plot([0, w], [y, y], color=INK, lw=1.5 + j_(0.1))
    for ri, (cells, h) in enumerate(laid):
        h = h * (1 + j_(0.03))
        for j, lines in enumerate(cells):
            _, bold, hot = rows[ri][j]
            key = None if ri == 0 else (f"{ri - 1},{j}")
            if ri > 0 and key in hl:
                ax.add_patch(plt.Rectangle((xs[j] + 0.01, y + 0.01), cw[j] - 0.02, h - 0.02, color="C1", alpha=0.3, lw=0))
            elif ri > 0 and key in spec["colors"]:
                ax.add_patch(plt.Rectangle((xs[j] + 0.01, y + 0.01), cw[j] - 0.02, h - 0.02, color="C2", alpha=0.3, lw=0))
            ax.text(xs[j] + PAD_X + j_(0.012), y + h / 2 + j_(0.01), "\n".join(lines), fontsize=fs, va="center", ha="left", linespacing=1.15,
                    fontweight="bold" if (ri == 0) else "normal", color=INK)
        y += h
        if ri == 0:
            ax.plot([0, w], [y, y], color=INK, lw=0.8 + j_(0.1))
        elif ri < len(laid) - 1:
            ax.plot([0, w], [y, y], color=RULE, lw=0.4)
    ax.plot([0, w], [y, y], color=INK, lw=1.2 + j_(0.1))
    ax.set_ylim(y + 0.03, 0)
    fig.savefig(f"tables/{spec['id']}.png", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs("tables", exist_ok=True)
    specs = json.load(open("tables_spec.json"))
    for sp in specs:
        render(sp)
    print(len(specs), "tables")
