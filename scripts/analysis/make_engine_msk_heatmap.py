from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import cli, load_combos

args = cli("engine x msk heatmap")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

df = load_combos(args.data)
d = df.drop_duplicates(subset=["ID", "Engine", "MSK"])
ct = pd.crosstab(d["MSK"], d["Engine"])
ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).index]
ct = ct[ct.sum(axis=0).sort_values(ascending=False).index]

sns.set_theme(style="white", font_scale=1.0)
norm = mcolors.PowerNorm(gamma=0.35, vmin=0, vmax=ct.values.max())
fig, ax = plt.subplots(figsize=(7.2, 12))
sns.heatmap(ct, cmap="BuPu", norm=norm, annot=True, fmt="d", linewidths=0.6,
            linecolor="white", cbar=False, annot_kws={"size": 10}, ax=ax)
ax.set_title(f"Engine × Musculoskeletal system combinations "
             f"(n={d['ID'].nunique()} papers)", fontsize=12, pad=10)
ax.set_xlabel("Physics engine")
ax.set_ylabel("Musculoskeletal system")
ax.set_xticklabels(ct.columns, rotation=0)
ax.set_yticklabels(ct.index, rotation=0)
fig.tight_layout()
fig.savefig(out_dir / "heatmap_engine_msk.png", dpi=args.dpi, bbox_inches="tight")
plt.close(fig)

with pd.ExcelWriter(out_dir / "engine_msk_crosstab.xlsx", engine="openpyxl") as w:
    ct.to_excel(w, sheet_name="engine_msk_counts")
