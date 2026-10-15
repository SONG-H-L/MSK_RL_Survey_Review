from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import cli, load_studies
from config import COL_PIO_FLAG, PERIODS, PI_OUTPUTS

args = cli("policy output x period heatmap")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

OUTPUT_SHORT = ["Muscle activation", "Muscle excitation", "Kinematic",
                "Synergy", "Muscle length"]

s1 = load_studies(args.data)
for c in PI_OUTPUTS + [COL_PIO_FLAG]:
    s1[c] = pd.to_numeric(s1[c], errors="coerce").fillna(0).astype(int)
pio = s1[s1[COL_PIO_FLAG] == 1]

period_n = pio.groupby("Period", observed=True)["ID"].nunique()
rows = []
for out_col in PI_OUTPUTS:
    g = pio.groupby("Period", observed=True)[out_col].sum()
    rows.append([int(g.get(p, 0)) for p in PERIODS])
cnt = pd.DataFrame(rows, index=OUTPUT_SHORT, columns=PERIODS)
pct = cnt / period_n.reindex(PERIODS) * 100

sns.set_theme(style="white", font_scale=1.0)
fig, ax = plt.subplots(figsize=(9.29, 5.2))
annot = cnt.astype(object)
for c in PERIODS:
    annot[c] = [f"{int(v)} ({v / period_n[c] * 100:.1f}%)" for v in cnt[c]]
sns.heatmap(pct, cmap="Blues", vmin=0, annot=annot.values, fmt="",
            linewidths=0.6, linecolor="white", cbar=False,
            annot_kws={"size": 11}, ax=ax)
ax.set_title(f"Policy output types by period — clearly reported studies (n={len(pio)})",
             fontsize=12, pad=10)
ax.set_xlabel("")
ax.set_ylabel("Policy output type")
ax.set_xticklabels([f"{p}\n(n={int(period_n[p])} studies)" for p in PERIODS], rotation=0)
note_text = ("Cell: number of studies (% of studies in that period);  n per period: "
             + ", ".join(f"{q} = {int(period_n[q])}" for q in PERIODS))
ax.text(0.0, -0.14, note_text, transform=ax.transAxes, fontsize=8.5,
        color="#777777", ha="left")
fig.tight_layout()
fig.savefig(out_dir / "policy_output_by_period.png", dpi=args.dpi, bbox_inches="tight")
plt.close(fig)

with pd.ExcelWriter(out_dir / "poutput_by_period.xlsx", engine="openpyxl") as w:
    cnt.to_excel(w, sheet_name="counts")
    pct.round(1).to_excel(w, sheet_name="pct")
