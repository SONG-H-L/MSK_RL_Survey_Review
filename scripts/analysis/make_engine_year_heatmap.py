from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import cli, load_combos

args = cli("engine x year heatmap")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)
YEARS = list(range(2017, 2026))

df = load_combos(args.data)
pool_frames = {"no": df[df["Comp"] == "No"], "yes": df[df["Comp"] != "No"]}
POOLS = {"no": {"label": "Non-competition (Competition origin = No)", "cmap": "Blues"},
         "yes": {"label": "Competition-origin (Competition origin ≠ No)", "cmap": "Purples"}}

tables = {}
for key, sub in pool_frames.items():
    sub = sub.drop_duplicates(subset=["ID", "Engine", "Year"])
    counts = (sub.pivot_table(index="Engine", columns="Year", values="ID",
                              aggfunc="nunique", fill_value=0)
              .reindex(columns=YEARS, fill_value=0))
    tables[key] = {"counts": counts, "n": sub["ID"].nunique()}

engine_order = (sum(t["counts"].sum(axis=1) for t in tables.values())
                .sort_values(ascending=False).index.tolist())
for key in tables:
    counts = tables[key]["counts"].reindex(index=engine_order, fill_value=0)
    tables[key]["counts"] = counts
    pct_full = counts / counts.sum(axis=0) * 100
    pct = pct_full[counts.columns[counts.sum(axis=0) > 0]]
    tables[key]["pct"] = pct
    annot = pct.copy().astype(object)
    for c in pct.columns:
        annot[c] = pct[c].map(lambda v: f"{v:.1f}")
    tables[key]["pct_annot"] = annot
    tables[key]["pct_full"] = pct_full

sns.set_theme(style="white", font_scale=1.0)


def draw(data, cmap, fmt, title, path, annot_data=None):
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    sns.heatmap(data, cmap=cmap, vmin=0, annot=annot_data if annot_data is not None else True,
                fmt=fmt, linewidths=0.6, linecolor="white", square=True, cbar=False,
                annot_kws={"size": 10}, ax=ax)
    ax.set_title(title, fontsize=12, pad=10)
    ax.set_xlabel("Year")
    ax.set_ylabel("Physics engine")
    ax.set_xticklabels([str(c) for c in data.columns], rotation=0)
    ax.set_yticklabels(data.index, rotation=0)
    fig.tight_layout()
    fig.savefig(path, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)


for key, cfg in POOLS.items():
    t = tables[key]
    draw(t["counts"], cfg["cmap"], "d",
         f"Engine popularity by year — {cfg['label']} (n={t['n']})",
         out_dir / f"heatmap_{key}_abs.png")
    draw(t["pct"], cfg["cmap"], "",
         f"Engine share by year (%) — {cfg['label']} (n={t['n']})",
         out_dir / f"heatmap_{key}_pct.png", annot_data=t["pct_annot"])

with pd.ExcelWriter(out_dir / "engine_year_pool_data.xlsx", engine="openpyxl") as w:
    for key in tables:
        tables[key]["counts"].to_excel(w, sheet_name=f"{key}_counts")
        tables[key]["pct_full"].round(1).to_excel(w, sheet_name=f"{key}_pct")
