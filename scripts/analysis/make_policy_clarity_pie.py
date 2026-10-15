from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import cli, load_studies
from config import COL_PIO_FLAG

args = cli("policy io clarity pie")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

s1 = load_studies(args.data)
flag = COL_PIO_FLAG
s1[flag] = pd.to_numeric(s1[flag], errors="coerce").fillna(0).astype(int)

n_clear = int((s1[flag] == 1).sum())
n_unclear = len(s1) - n_clear

fig, ax = plt.subplots(figsize=(9.5, 6.6))
wedges, _ = ax.pie([n_clear, n_unclear], colors=["#cbd5e0", "#4a5568"],
                   startangle=90, counterclock=False,
                   wedgeprops=dict(width=0.46, edgecolor="white", linewidth=1.8))
labels = [f"Clearly reported\n{n_clear} ({n_clear / len(s1) * 100:.1f}%)",
          f"Not clearly reported\n{n_unclear} ({n_unclear / len(s1) * 100:.1f}%)"]
ax.legend(wedges, labels, loc="center", fontsize=10.5, frameon=False,
          handlelength=1.1, handleheight=1.1, labelspacing=0.5, borderpad=0.2)
ax.set_aspect("equal")
fig.savefig(out_dir / "policy_io_clarity_pie.png", dpi=args.dpi, bbox_inches="tight")
plt.close(fig)

pd.DataFrame({"n": [n_clear, n_unclear]},
             index=["clear (1)", "not clear (0)"]).to_excel(
    out_dir / "policy_clarity.xlsx")
