from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib_venn import venn3

from common import cli, load_studies
from config import CONTRIBUTIONS

args = cli("contribution venn")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

SHORT = ("Methodological", "Application", "Knowledge-generating")
COLORS = {"all": ("#4a5568", "#9dc3e6", "#cbd5e0"),
          "no": tuple(plt.cm.Blues(t)[:3] for t in (0.20, 0.50, 0.90))}

s1 = load_studies(args.data)
for c in CONTRIBUTIONS:
    s1[c] = pd.to_numeric(s1[c], errors="coerce").fillna(0).astype(int)

pools = {"all": s1, "no": s1[s1["Pool"] == "No"]}


def region_counts(sub):
    m, a, k = (sub[c] == 1 for c in CONTRIBUTIONS)
    return (int((m & ~a & ~k).sum()), int((a & ~m & ~k).sum()),
            int((m & a & ~k).sum()), int((k & ~m & ~a).sum()),
            int((m & k & ~a).sum()), int((a & k & ~m).sum()),
            int((m & a & k).sum()), int((~m & ~a & ~k).sum()))


rows = []
for key, sub in pools.items():
    r = region_counts(sub)
    fig, ax = plt.subplots(figsize=(8.6, 7.0))
    venn = venn3(subsets=r[:7], set_labels=SHORT, set_colors=COLORS[key], alpha=0.75, ax=ax)
    for t in venn.set_labels:
        t.set_fontsize(12)
        t.set_fontweight("bold")
    for t in venn.subset_labels:
        if t is not None:
            t.set_fontsize(13)
            t.set_fontweight("bold")
    title = (f"Contribution types of {len(sub)} studies (counts per region)" if key == "all"
             else f"Contribution types, Non-competition studies "
                   f"(Competition origin = No) (n={len(sub)})")
    ax.set_title(title, fontsize=12.5, pad=16)
    fig.savefig(out_dir / f"venn_contribution_{key}.png", dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)
    rows.append({"pool": key, "n": len(sub), "M_only": r[0], "A_only": r[1], "M&A": r[2],
                 "K_only": r[3], "M&K": r[4], "A&K": r[5], "M&A&K": r[6], "none": r[7]})

pd.DataFrame(rows).to_excel(out_dir / "contribution_venn.xlsx", index=False)
