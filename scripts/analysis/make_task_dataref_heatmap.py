from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import cli, pools_of, load_tasks

args = cli("task type x data reference heatmap")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)
REF_COLS = ["With data reference", "Without data reference"]

s2 = load_tasks(args.data)
tables = {}
for key, sub in pools_of(s2).items():
    ct = pd.crosstab(sub["TaskCat"], sub["DataRef"]).reindex(
        index=sub["TaskCat"].value_counts().index, columns=REF_COLS, fill_value=0)
    ct = ct.loc[ct[REF_COLS[0]].sort_values(ascending=False).index]
    tables[key] = {"counts": ct, "pct": ct.div(ct.sum(axis=1), axis=0) * 100,
                   "papers": sub["ID"].nunique(), "rows": len(sub)}

sns.set_theme(style="white", font_scale=1.0)
CMAP = "bone_r"


def draw_pool(key):
    ct, pct = tables[key]["counts"], tables[key]["pct"]
    norm_c = mcolors.PowerNorm(gamma=0.35, vmin=0, vmax=ct.values.max())
    norm_p = mcolors.Normalize(vmin=0, vmax=100)
    pct_annot = pct.copy().astype(object)
    for c in pct.columns:
        pct_annot[c] = pct[c].map(lambda v: f"{v:.1f}")
    fig, axes = plt.subplots(2, 1, figsize=(7.6, 0.52 * len(ct) + 3.2))
    sns.heatmap(ct, cmap=CMAP, norm=norm_c, annot=True, fmt="d", linewidths=0.6,
                linecolor="white", cbar=False, annot_kws={"size": 10}, ax=axes[0])
    sns.heatmap(pct, cmap=CMAP, norm=norm_p, annot=pct_annot, fmt="", linewidths=0.6,
                linecolor="white", cbar=False, annot_kws={"size": 10}, ax=axes[1])
    for ax in axes:
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_yticklabels(ct.index, rotation=0)
        ax.set_xticklabels(REF_COLS, rotation=0)
    fig.tight_layout(h_pad=1.6)
    fig.savefig(out_dir / f"task_dataref_{key}.png", dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)


for key in ["total", "no"]:
    draw_pool(key)

with pd.ExcelWriter(out_dir / "task_dataref.xlsx", engine="openpyxl") as w:
    for key in tables:
        tables[key]["counts"].to_excel(w, sheet_name=f"{key}_counts")
        tables[key]["pct"].round(1).to_excel(w, sheet_name=f"{key}_pct")
