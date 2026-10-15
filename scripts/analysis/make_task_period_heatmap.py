from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import cli, load_tasks, pools_of
from config import PERIODS

args = cli("task type x period heatmap")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

s2 = load_tasks(args.data)
pools = pools_of(s2)


def crosstab_pool(sub):
    return pd.crosstab(sub["TaskCat"], sub["Period"]).reindex(columns=PERIODS, fill_value=0)

ct_total = crosstab_pool(pools["total"])
parent_of = ct_total.index.to_series().str.split(r" \(").str[0]
parent_order = ct_total.groupby(parent_of).sum().sum(axis=1).sort_values(
    ascending=False).index.tolist()
_tmp = pd.DataFrame({"_parent": parent_of, "_total": ct_total.sum(axis=1)})
_tmp["_prank"] = _tmp["_parent"].map({p: i for i, p in enumerate(parent_order)})
ROW_ORDER = _tmp.sort_values(["_prank", "_total"], ascending=[True, False]).index.tolist()

tables = {}
for key, sub in pools.items():
    ct = crosstab_pool(sub).reindex(index=ROW_ORDER, fill_value=0)
    tables[key] = {"counts": ct, "pct": ct / ct.sum(axis=0) * 100,
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
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 0.62 * len(ct) + 3.4))
    sns.heatmap(ct, cmap=CMAP, norm=norm_c, annot=True, fmt="d", linewidths=0.6,
                linecolor="white", cbar=False, annot_kws={"size": 10}, ax=axes[0])
    sns.heatmap(pct, cmap=CMAP, norm=norm_p, annot=pct_annot, fmt="", linewidths=0.6,
                linecolor="white", cbar=False, annot_kws={"size": 10}, ax=axes[1])
    for ax in axes:
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_yticklabels(ct.index, rotation=0)
        ax.set_xticklabels(PERIODS, rotation=0)
    fig.tight_layout(h_pad=1.6)
    fig.savefig(out_dir / f"task_pool_{key}.png", dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)


for key in ["total", "no"]:
    draw_pool(key)

with pd.ExcelWriter(out_dir / "task_distribution.xlsx", engine="openpyxl") as w:
    freq = (s2.groupby("ID").size().rename("task_count")
            .to_frame().join(s2.groupby("ID")["Pool"].first()).sort_index())
    freq.to_excel(w, sheet_name="per_id_task_freq")
    for key in tables:
        tables[key]["counts"].to_excel(w, sheet_name=f"{key}_counts")
        tables[key]["pct"].round(1).to_excel(w, sheet_name=f"{key}_pct")
