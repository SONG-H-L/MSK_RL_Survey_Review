from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import upsetplot

from common import cli, load_studies
from config import COL_PIO_FLAG, PARADIGMS, PI_INPUTS

args = cli("policy inputs / paradigms upset")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

INPUT_SHORT = ["Joint & segment kinematics", "Muscle-related states",
               "Time or phase", "Historical information", "Contact"]
PARA_SHORT = ["Behavior cloning", "Bio-inspired", "Exploration",
              "Curriculum learning", "Multi-task learning"]

s1 = load_studies(args.data)
for c in PI_INPUTS + PARADIGMS + [COL_PIO_FLAG]:
    s1[c] = pd.to_numeric(s1[c], errors="coerce").fillna(0).astype(int)
pio = s1[s1[COL_PIO_FLAG] == 1]


def build_upset(sub, flag_cols, short_names, out_name, bar_color):
    bool_df = sub[flag_cols].astype(bool)
    bool_df.columns = short_names
    up = bool_df.groupby(list(bool_df.columns)).size()
    upset = upsetplot.UpSet(up, sort_by="cardinality", sort_categories_by="cardinality",
                            show_counts="%d", show_percentages=False, element_size=22,
                            totals_plot_elements=4, min_degree=1, facecolor=bar_color)
    fig = plt.figure(figsize=(13.5, 7.0))
    out_axes = upset.plot(fig=fig)
    xmin, xmax = out_axes["totals"].get_xlim()
    out_axes["totals"].set_xlim(xmin, xmin + (xmax - xmin) * 1.75)
    out_axes["matrix"].tick_params(labelsize=12)
    fig.savefig(out_dir / out_name, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)


build_upset(pio, PI_INPUTS, INPUT_SHORT, "upset_policy_inputs.png", "#4a5568")
build_upset(s1, PARADIGMS, PARA_SHORT, "upset_paradigms.png", "#cbd5e0")

combo_rows = []
for name, sub, cols, shorts in [("policy_inputs", pio, PI_INPUTS, INPUT_SHORT),
                                ("paradigms", s1, PARADIGMS, PARA_SHORT)]:
    b = sub[cols].astype(bool)
    for ix, n in b.groupby(list(b.columns)).size().items():
        combo_rows.append({"dataset": name,
                           "combo": " + ".join([s for s, on in zip(shorts, ix) if on]),
                           "studies": int(n)})

pd.DataFrame(combo_rows).to_excel(out_dir / "policy_paradigm_combos.xlsx", index=False)
