from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import POOL_LABEL, cli, pools_of, load_tasks

args = cli("tasks per study")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)
C_BAR = "#8b9db3"
FS_ANN, FS_LAB, FS_TITLE, FS_TICK = 20, 25, 27, 23

s2 = load_tasks(args.data)
per_id = (s2.groupby("ID").size().rename("task_count")
          .to_frame().join(s2.groupby("ID")["Pool"].first()).sort_index())
pools = pools_of(per_id)
freq_tables = {k: v["task_count"].value_counts().sort_index() for k, v in pools.items()}

for key, freq in freq_tables.items():
    n_papers = int(freq.sum())
    xs = list(range(1, int(pools[key]["task_count"].max()) + 1))
    ys = [int(freq.get(x, 0)) for x in xs]
    n_tasks = int((np.asarray(xs) * np.asarray(ys)).sum())
    top = max(ys) * 3
    shown = [x for x in xs if freq.get(x, 0) > 0]

    fig, ax = plt.subplots(figsize=(7.6, 9.4))
    fig.subplots_adjust(left=0.235, right=0.965, top=0.715, bottom=0.13)
    ax.bar(xs, ys, color=C_BAR, width=0.72, edgecolor="white")
    ax_h_pt = 0.585 * 9.4 * 72
    dec_pt = ax_h_pt / np.log10(top / 0.8)
    for x, y in zip(xs, ys):
        if y > 0:
            ax.text(x, y * 10 ** (16 / dec_pt), f"{y} ({y / n_papers * 100:.1f}%)",
                    ha="center", va="bottom", rotation=90, fontsize=FS_ANN)
    ax.set_xlabel("Number of tasks per study", fontsize=FS_LAB)
    ax.set_ylabel("Number of studies", fontsize=FS_LAB)
    ax.set_title(f"Tasks per study\n— {POOL_LABEL[key]}\n"
                 f"(n={n_papers} studies, {n_tasks} tasks)", fontsize=FS_TITLE, pad=80)
    ax.set_xticks(shown)
    ax.set_yscale("log")
    ax.set_ylim(0.8, top)
    yticks = [t for t in [1, 2, 5, 10, 20, 50, 100, 200, 500] if t < top]
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(t) for t in yticks])
    ax.tick_params(labelsize=FS_TICK, width=2.4, length=9)
    ax.minorticks_off()
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_linewidth(2.0)
    ax.yaxis.grid(True, linewidth=1.3, color="#d9d9d9")
    ax.set_axisbelow(True)
    fig.savefig(out_dir / f"task_freq_{key}.png", dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)

with pd.ExcelWriter(out_dir / "task_freq_by_pool.xlsx", engine="openpyxl") as w:
    per_id.to_excel(w, sheet_name="per_id_detail")
    for key, freq in freq_tables.items():
        out = freq.rename_axis("task_count").reset_index(name="papers")
        out["pct_of_papers"] = (out["papers"] / out["papers"].sum() * 100).round(1)
        out.to_excel(w, sheet_name=f"{key}_freq", index=False)
