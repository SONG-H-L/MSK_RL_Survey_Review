from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import upsetplot

from common import cli, load_tasks
from config import REWARD_ATOMS

args = cli("reward atoms upset")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

s2 = load_tasks(args.data)
for c in REWARD_ATOMS:
    s2[c] = pd.to_numeric(s2[c], errors="coerce").fillna(0).astype(int)

clear_all = s2[s2.Clearly == "1"].copy()
clear_all["tc"] = clear_all.groupby("ID")["ID"].transform("size")
sensitivity = clear_all[(clear_all.Pool == "No") & (clear_all.tc == 1)].copy()

runs = [
    ("global", "main", (16, 9), 2, ("#cbd5e0", "#4a5568"), clear_all),
    ("sensitivity", "full", (25.2, 9.5), None, ("#b4cfe7", "#7fa8cf"), sensitivity),
]


def build_upset(sub, out_name, fig_size, min_subset_size, deg_shades):
    deg_cmap = cm.colors.LinearSegmentedColormap.from_list("deg_shades", list(deg_shades))
    bool_df = sub[REWARD_ATOMS].astype(bool)
    up = bool_df.groupby(list(bool_df.columns)).size()
    upset = upsetplot.UpSet(
        up, sort_by="cardinality", sort_categories_by="cardinality",
        show_counts="%d", show_percentages=False, element_size=20,
        totals_plot_elements=4, min_degree=1, min_subset_size=min_subset_size,
        facecolor="auto", other_dots_color="white")
    max_deg = int(max(len(ix) for ix in up.index))
    for dg in range(1, max_deg + 1):
        upset.style_subsets(min_degree=dg, max_degree=dg,
                            facecolor=deg_cmap((dg - 1) / max(max_deg - 1, 1)))
    fig = plt.figure(figsize=fig_size)
    out_axes = upset.plot(fig=fig)
    mx = out_axes["matrix"]
    for coll in mx.collections:
        fc = coll.get_facecolors()
        if len(fc):
            white = np.all(fc[:, :3] > 0.98, axis=1)
            if white.any():
                fc[white, 3] = 0.0
                coll.set_facecolors(fc)
    fig.savefig(out_dir / out_name, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)


for k, suffix, size, mss, shades, d in runs:
    build_upset(d, f"upset_{k}_{suffix}.png", size, mss, shades)

combo_rows = []
for k, _, _, _, _, d in runs:
    bool_df = d[REWARD_ATOMS].astype(bool)
    for ix, n in bool_df.groupby(list(bool_df.columns)).size().items():
        combo_rows.append({"dataset": k,
                           "combo": " + ".join([a for a, on in zip(REWARD_ATOMS, ix) if on]),
                           "tasks": int(n)})
pd.DataFrame(combo_rows).to_excel(out_dir / "reward_combos.xlsx", index=False)
