import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.cm as cm
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from common import cli, load_tasks
from config import REWARD_ATOMS

args = cli("task-reward bipartite network")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

EDGE_CMAP = cm.colors.LinearSegmentedColormap.from_list(
    "edge_blues", plt.cm.Blues(np.linspace(0.18, 0.80, 256)))
LBL_COLOR = "#4a5568"

s2 = load_tasks(args.data)
for c in REWARD_ATOMS:
    s2[c] = pd.to_numeric(s2[c], errors="coerce").fillna(0).astype(int)

clear_all = s2[s2.Clearly == "1"].copy()
clear_all["tc"] = clear_all.groupby("ID")["ID"].transform("size")
datasets = {"global": clear_all,
            "sensitivity": clear_all[(clear_all.Pool == "No") & (clear_all.tc == 1)].copy()}


def wrap_label(s, width=19):
    s = s.replace("\u2013", "-").replace("\u00a0", " ")
    return "\n".join(textwrap.wrap(" ".join(s.split()), width=width,
                                   break_long_words=True, break_on_hyphens=True))


def build_bipartite(sub, out_name):
    edges = sub[["TaskCat"] + REWARD_ATOMS].melt(
        id_vars="TaskCat", var_name="Reward_atom", value_name="value")
    edges = edges[edges.value == 1]
    task_nodes = sorted(edges.TaskCat.unique())
    reward_nodes = sorted(edges.Reward_atom.unique())
    weight_data = edges.groupby(["TaskCat", "Reward_atom"]).size().reset_index(name="weight")

    B = nx.Graph()
    B.add_nodes_from(task_nodes, bipartite=0)
    B.add_nodes_from(reward_nodes, bipartite=1)
    for _, r in weight_data.iterrows():
        B.add_edge(r.TaskCat, r.Reward_atom, weight=float(r.weight))

    degree = dict(B.degree())
    wdegree = dict(B.degree(weight="weight"))
    left_nodes = sorted(task_nodes, key=lambda x: wdegree.get(x, 0))
    right_nodes = sorted(reward_nodes, key=lambda x: wdegree.get(x, 0))

    total_height = (max(len(left_nodes), len(right_nodes)) - 1) * 1.15
    y_left = np.linspace(-total_height / 2, total_height / 2, len(left_nodes))
    y_right = np.linspace(-total_height / 2, total_height / 2, len(right_nodes))
    pos = {n: (0.0, y) for n, y in zip(left_nodes, y_left)}
    pos.update({n: (1.35, y) for n, y in zip(right_nodes, y_right)})

    right_w = np.array([wdegree.get(n, 0.0) for n in right_nodes], dtype=float)
    right_sizes = (50 + (right_w - right_w.min()) /
                   max(right_w.max() - right_w.min(), 1) * (500 - 50)) if len(right_w) else []
    edge_weights = [B[u][v].get("weight", 1.0) for u, v in B.edges()]
    min_w, max_w = (min(edge_weights), max(edge_weights)) if edge_weights else (1, 1)

    fig, ax = plt.subplots(figsize=(10.6, 12))
    nx.draw_networkx_nodes(B, pos, nodelist=left_nodes, node_color="#4a5568",
                           node_size=120, node_shape="s", edgecolors="#2f3b4c",
                           alpha=0.85, ax=ax)
    nx.draw_networkx_nodes(B, pos, nodelist=right_nodes, node_color="#cbd5e0",
                           node_size=right_sizes, edgecolors="#8b9db3", alpha=0.85, ax=ax)
    for u, v in B.edges():
        w = B[u][v].get("weight", 1.0)
        norm = (w - min_w) / (max_w - min_w) if max_w > min_w else 0.5
        nx.draw_networkx_edges(B, pos, edgelist=[(u, v)], width=0.75 + 1.95 * norm,
                               alpha=0.8, edge_color=EDGE_CMAP(norm), ax=ax)

    left_labels = {n: wrap_label(n) + "\n(k=" + str(degree[n]) + ")" for n in left_nodes}
    right_labels = {n: wrap_label(n) + "\n(k=" + str(degree[n])
                        + ", w=" + str(int(round(wdegree[n]))) + ")" for n in right_nodes}
    for labels, ha in ((left_labels, "right"), (right_labels, "left")):
        drawn = nx.draw_networkx_labels(B, pos, labels=labels, font_size=13.5,
                                        font_weight="bold", verticalalignment="center",
                                        horizontalalignment=ha, ax=ax)
        for tt in drawn.values():
            tt.set_color(LBL_COLOR)

    if edge_weights and max_w > min_w:
        sm = plt.cm.ScalarMappable(cmap=EDGE_CMAP, norm=plt.Normalize(min_w, max_w))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation="vertical", shrink=0.5, pad=0.01)
        cbar.set_label("Edge Weight", fontsize=10, fontweight="bold")
        cbar.ax.tick_params(labelsize=9)

    leg = [mlines.Line2D([0], [0], marker="s", linestyle="none", markerfacecolor="#4a5568",
                         markeredgecolor="#2f3b4c", markersize=11, label="Task category (square)"),
           mlines.Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="#cbd5e0",
                         markeredgecolor="#8b9db3", markersize=11, label="Reward term (circle)")]
    fig.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.55, 1.0),
               ncol=2, frameon=False, fontsize=11, title="Node type")
    ax.set_axis_off()
    ax.set_xlim(-0.95, 2.30)
    y_vals = [p[1] for p in pos.values()]
    ax.set_ylim(min(y_vals) - 1.0, max(y_vals) + 1.0)
    ax.text(0.675, min(y_vals) - 0.55,
            f"Total: {len(sub)} clear tasks ({sub.ID.nunique()} studies)",
            ha="center", va="center", fontsize=12, color="#4a5568")
    fig.tight_layout()
    fig.savefig(out_dir / out_name, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)

    adj = nx.to_pandas_adjacency(B, nodelist=left_nodes + right_nodes, weight="weight")
    return adj.loc[left_nodes, right_nodes]


adjs = {}
for k, d in datasets.items():
    adjs[k] = build_bipartite(d, f"bipartite_{k}.png")

with pd.ExcelWriter(out_dir / "task_reward_adjacency.xlsx", engine="openpyxl") as w:
    for k in adjs:
        adjs[k].to_excel(w, sheet_name=f"{k}_adjacency")
