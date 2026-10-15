from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import upsetplot

from common import cli, load_studies
from config import EVALUATIONS

args = cli("evaluation upset")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

EVAL_SHORT = ["Kinematics", "Torque", "Performance",
              "Muscle act./Metabolic", "GRF", "Qual. visual"]
EVALS = list(zip(EVALUATIONS, EVAL_SHORT))
DEG_COLORS = {"all": ("#c9ccd2", "#3a3f47"),
              "no": (mcolors.to_hex(plt.cm.Blues(0.12)),
                     mcolors.to_hex(plt.cm.Blues(0.50)))}

s1 = load_studies(args.data)
for c, _ in EVALS:
    s1[c] = pd.to_numeric(s1[c], errors="coerce").fillna(0).astype(int)

pools = {"all": s1, "no": s1[s1["Pool"] == "No"]}


def build_upset(sub, out_name, deg_colors):
    flag_cols = [c for c, _ in EVALS]
    bool_df = sub[flag_cols].astype(bool)
    bool_df.columns = [s for _, s in EVALS]
    up = bool_df.groupby(list(bool_df.columns)).size()

    upset = upsetplot.UpSet(up, sort_by="cardinality", sort_categories_by="cardinality",
                            show_counts="%d", show_percentages=False, element_size=22,
                            totals_plot_elements=3, min_degree=1)
    deg_cmap = mcolors.LinearSegmentedColormap.from_list("bone_deg", deg_colors)
    max_deg = int(max(len(ix) for ix in up.index))
    for d in range(1, max_deg + 1):
        upset.style_subsets(min_degree=d, max_degree=d,
                            facecolor=deg_cmap((d - 1) / max(max_deg - 1, 1)))
    fig = plt.figure(figsize=(13.5, 7.0))
    out_axes = upset.plot(fig=fig)
    xmin, xmax = out_axes["totals"].get_xlim()
    out_axes["totals"].set_xlim(xmin, xmin + (xmax - xmin) * 1.75)
    out_axes["matrix"].tick_params(labelsize=12)
    fig.savefig(out_dir / out_name, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)


rows = []
with pd.ExcelWriter(out_dir / "eval_upset_summary.xlsx", engine="openpyxl") as w:
    for key, sub in pools.items():
        build_upset(sub, f"upset_eval_{key}.png", DEG_COLORS[key])
        b = sub[[c for c, _ in EVALS]].astype(bool)
        b.columns = [s for _, s in EVALS]
        b.groupby(list(b.columns)).size().to_excel(w, sheet_name=f"{key}_combos")
        sizes = {s: int(sub[c].sum()) for c, s in EVALS}
        rows.append({"pool": key, "n": len(sub), **sizes})

pd.DataFrame(rows).to_excel(out_dir / "eval_set_sizes.xlsx", index=False)
