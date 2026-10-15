from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import cli
from config import COL_ALGO, PERIODS, SHEET_ALGO

args = cli("algo x period heatmap")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

a = pd.read_excel(args.data, sheet_name=SHEET_ALGO).rename(columns={COL_ALGO: "Algo"})
a["Algo"] = a["Algo"].astype(str).str.strip()
a.loc[a["Algo"].str.lower() == "model-based rl", "Algo"] = "Model-based RL"
a = a[a["Algo"] != "-"].copy()
a["Period"] = a["Years"].astype(int).map(
    lambda y: PERIODS[0] if y <= 2019 else PERIODS[1] if y <= 2022 else PERIODS[2])

d = a.drop_duplicates(subset=["ID", "Algo", "Period"])
ct = pd.crosstab(d["Algo"], d["Period"]).reindex(columns=PERIODS, fill_value=0)
ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).index]
ct_t = ct.T
ct_t.columns.name = None
pct_t = (ct / ct.sum(axis=0) * 100).T
pct_annot = pct_t.copy().astype(object)
for c in pct_t.columns:
    pct_annot[c] = pct_t[c].map(lambda v: f"{v:.1f}")

sns.set_theme(style="white", font_scale=1.0)
CMAP = "bone_r"
norm_abs = mcolors.PowerNorm(gamma=0.35, vmin=0, vmax=ct_t.values.max())
norm_pct = mcolors.Normalize(vmin=0, vmax=100)

fig, ax = plt.subplots(figsize=(10, 3.8))
sns.heatmap(pct_t, cmap=CMAP, norm=norm_pct, annot=pct_annot, fmt="",
            linewidths=0.6, linecolor="white", square=True, cbar=False,
            annot_kws={"size": 11}, ax=ax)
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_yticklabels(pct_t.index, rotation=0)
ax.set_xticklabels(pct_t.columns, rotation=30, ha="right")
fig.tight_layout()
fig.savefig(out_dir / "heatmap_algo_pct.png", dpi=args.dpi, bbox_inches="tight")
plt.close(fig)

fig, axes = plt.subplots(2, 1, figsize=(10.5, 8.4))
sns.heatmap(ct_t, cmap=CMAP, norm=norm_abs, annot=True, fmt="d", linewidths=0.6,
            linecolor="white", square=True, cbar=False, annot_kws={"size": 11}, ax=axes[0])
sns.heatmap(pct_t, cmap=CMAP, norm=norm_pct, annot=pct_annot, fmt="", linewidths=0.6,
            linecolor="white", square=True, cbar=False, annot_kws={"size": 11}, ax=axes[1])
for ax in axes:
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_yticklabels(pct_t.index, rotation=0)
    ax.set_xticklabels(pct_t.columns, rotation=30, ha="right")
fig.tight_layout(h_pad=2.2)
fig.savefig(out_dir / "heatmap_algo_stacked.png", dpi=args.dpi, bbox_inches="tight")
plt.close(fig)

with pd.ExcelWriter(out_dir / "algo_period_crosstab.xlsx", engine="openpyxl") as w:
    ct.to_excel(w, sheet_name="algo_period_counts")
    (ct / ct.sum(axis=0) * 100).round(1).to_excel(w, sheet_name="algo_period_pct")
