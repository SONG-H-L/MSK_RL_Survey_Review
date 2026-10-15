from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import cli, pools_of, load_tasks

args = cli("data reference hierarchy")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)
REF_COLS = ["With data reference", "Without data reference"]
C_WITH, C_WITHOUT = "#4a5568", "#cbd5e0"
PIE_POS = {"total": [0.58, 0.10, 0.30, 0.28], "no": [0.58, 0.07, 0.36, 0.30]}

s2 = load_tasks(args.data)
pools = pools_of(s2)


def layer_stats(sub, key_col):
    g = sub.groupby(key_col)
    out = pd.DataFrame({
        "tasks": g.size(),
        "with_ref": g.apply(lambda x: (x["DataRef"] == REF_COLS[0]).sum()),
        "without_ref": g.apply(lambda x: (x["DataRef"] == REF_COLS[1]).sum()),
    })
    out["rate_pct"] = (out["with_ref"] / out["tasks"] * 100).round(1)
    return out.sort_values("tasks", ascending=False)


hier = {k: {"L1": layer_stats(s, "Task type"), "L2": layer_stats(s, "TaskCat")}
        for k, s in pools.items()}


def build_rows(key):
    l1, l2 = hier[key]["L1"], hier[key]["L2"]
    rows = []
    for t in l1.index:
        rows.append((t, True, int(l1.loc[t, "tasks"]), int(l1.loc[t, "with_ref"]),
                     int(l1.loc[t, "without_ref"]), float(l1.loc[t, "rate_pct"])))
        for c in l2[l2.index.str.startswith(t + " ")].index:
            rows.append((c[c.index("("):], False, int(l2.loc[c, "tasks"]),
                         int(l2.loc[c, "with_ref"]), int(l2.loc[c, "without_ref"]),
                         float(l2.loc[c, "rate_pct"])))
    return rows


def draw_hier(key):
    rows = build_rows(key)
    n = len(rows)
    with_v = np.array([r[3] for r in rows], dtype=float)
    without_v = np.array([r[4] for r in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(9.2, 0.46 * n + 1.6))
    y = np.arange(n)[::-1]
    ax.barh(y, with_v, color=C_WITH, label=REF_COLS[0], height=0.62)
    ax.barh(y, without_v, left=with_v, color=C_WITHOUT, label=REF_COLS[1], height=0.62)
    pool_total = int(hier[key]["L1"]["tasks"].sum())
    for i in range(n):
        yi = n - 1 - i
        w, wo = with_v[i], without_v[i]
        tot = int(w + wo)
        if w > 0:
            ax.text(w / 2, yi, str(int(w)), ha="center", va="center",
                    color="white", fontsize=9)
        if wo > 0:
            ax.text(w + wo / 2, yi, str(int(wo)), ha="center", va="center",
                    color="#333333", fontsize=9)
        ax.text(w + wo + 0.6, yi, f"{rows[i][5]:.1f}%", va="center",
                fontsize=8.5, color="#666666")
        ax.text(tot / 2, yi + 0.34, f"{tot} ({tot / pool_total * 100:.1f}%)",
                ha="center", va="bottom", fontsize=8.5, color="#4a5568")
    X_TRUNK, X_END = -0.55, -0.12
    l1_idx = [i for i, r in enumerate(rows) if r[1]]
    for i_p, i_next in zip(l1_idx, l1_idx[1:] + [n]):
        yi_p = n - 1 - i_p
        child_ys = [n - 1 - j for j in range(i_p + 1, i_next)]
        if not child_ys:
            continue
        ax.plot([X_TRUNK, X_TRUNK], [yi_p, child_ys[-1]], color="#aaaaaa", lw=0.9, clip_on=False)
        ax.plot([X_TRUNK, X_END], [yi_p, yi_p], color="#aaaaaa", lw=0.9, clip_on=False)
        for yc in child_ys:
            ax.plot([X_TRUNK, X_END], [yc, yc], color="#aaaaaa", lw=0.9, clip_on=False)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    for i, tick in enumerate(ax.get_yticklabels()):
        if rows[i][1]:
            tick.set_fontweight("bold")
    ax.tick_params(axis="y", pad=10)
    ax.set_xlabel("Number of tasks")
    ax.set_xlim(-2.3, float((with_v + without_v).max()) * 1.14)
    ax.spines[["top", "right", "left"]].set_visible(False)
    sub = pools[key]
    with_n = int((sub["DataRef"] == REF_COLS[0]).sum())
    without_n = int((sub["DataRef"] == REF_COLS[1]).sum())
    pie_ax = ax.inset_axes(PIE_POS[key])
    wedges, _, _ = pie_ax.pie([with_n, without_n], colors=[C_WITH, C_WITHOUT],
                              autopct="%1.1f%%", pctdistance=1.22, startangle=90,
                              counterclock=False,
                              wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.5),
                              textprops=dict(fontsize=8.5, color="#4a5568"))
    pie_ax.set_title(f"Overall (n={with_n + without_n})", fontsize=9, color="#4a5568", pad=0)
    pie_ax.legend(wedges, REF_COLS, loc="lower center", bbox_to_anchor=(0.5, -0.18),
                  fontsize=7, frameon=False, ncol=1)
    fig.tight_layout()
    fig.savefig(out_dir / f"task_dataref_hier_{key}.png", dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)


for key in ["total", "no"]:
    draw_hier(key)

with pd.ExcelWriter(out_dir / "task_dataref_hier.xlsx", engine="openpyxl") as w:
    for key in pools:
        l1 = hier[key]["L1"].copy()
        l1.index.name = "Task type (L1)"
        l1.to_excel(w, sheet_name=f"{key}_L1")
        l2 = hier[key]["L2"].copy()
        l2.index.name = "Task type (Subcategory) (L2)"
        l2.to_excel(w, sheet_name=f"{key}_L2")
