import json
from pathlib import Path

import pandas as pd

from common import cli, load_combos

args = cli("sankey")
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)

df = load_combos(args.data)
df["Year"] = df["Year"].astype(str)

COMP_ORDER = ["NeurIPS 2017", "NeurIPS 2018", "NeurIPS 2019",
              "Myochallenge 2022", "Myochallenge 2023", "Myochallenge 2024",
              "No", "Not applicable"]
YEAR_ORDER = [str(y) for y in range(2017, 2026)]
ENGINE_ORDER = ["MuJoCo", "Simbody", "DART", "Hyfydy", "ODE"]
MSK_ORDER = ["Gait1422", "Gait0918", "Myohand", "Myolegs", "Lee et al.(2019)",
             "Myoarm", "MoBL_ARMS", "Myoelbow", "Kim et al.(2023;2025)",
             "H1622", "H0918", "MS-Human-700", "UitB", "Gait2354", "H2190",
             "SMS-Human", "Myoskeleton", "Myotorso"]
LDM_ORDER = ["No", "World model", "N/A"]
COMP_TITLES = {"No": "No competition", "Myochallenge 2022": "MyoChallenge 2022",
               "Myochallenge 2023": "MyoChallenge 2023", "Myochallenge 2024": "MyoChallenge 2024"}

NODE_COLORS = {
    "NeurIPS 2017": "#9ecae1", "NeurIPS 2018": "#4292c6", "NeurIPS 2019": "#08519c",
    "MyoChallenge 2022": "#e27e7e", "MyoChallenge 2023": "#ce5555", "MyoChallenge 2024": "#8e4825",
    "No competition": "#3c4a67", "Not applicable": "#c7cdd6",
    "2017": "#8dbbec", "2018": "#264fc9", "2019": "#006adb", "2020": "#cd7979",
    "2021": "#255610", "2022": "#4bb49a", "2023": "#263a54", "2024": "#101019", "2025": "#8e0b39",
    "MuJoCo": "#e15759", "Simbody": "#4e79a7", "DART": "#554fa1", "Hyfydy": "#2ceef2", "ODE": "#484848",
    "Gait1422": "#4e79a7", "Gait0918": "#a0cbe8", "Myohand": "#8667ad", "Myolegs": "#ffbe7d",
    "Lee et al.(2019)": "#474b85", "Myoarm": "#8cd17d", "MoBL_ARMS": "#b6992d", "Myoelbow": "#f1ce63",
    "Kim et al.(2023;2025)": "#499894", "H1622": "#86bcb6", "H0918": "#e15759",
    "MS-Human-700": "#ff9d9a", "UitB": "#79706e", "Gait2354": "#bab0ac", "H2190": "#d37295",
    "SMS-Human": "#fabfd2", "Myoskeleton": "#b07aa1", "Myotorso": "#d4a6c8",
    "No": "#a0a6b3", "World model": "#3ba6e8", "N/A": "#d9d9d9",
}
DEFAULT_COLOR = "#999999"

rows = []
for r in df.itertuples():
    c, y, e, m, l = (f"C:{r.Comp}", f"Y:{r.Year}", f"E:{r.Engine}",
                     f"M:{r.MSK}", f"L:{r.LDM}")
    rows += [(c, y), (y, e), (e, m), (m, l)]
flows = (pd.DataFrame(rows, columns=["source", "target"]).assign(value=1)
         .groupby(["source", "target"], as_index=False)["value"].sum())
flows["value"] = [int(v) for v in flows["value"]]


def order_layer(vc, order_titles, prefix):
    ordered = [f"{prefix}:{t}" for t in order_titles if t in vc.index]
    extra = [f"{prefix}:{t}" for t in vc.index if t not in order_titles]
    return ordered + extra


layer_raw = [
    (order_layer(df["Comp"].value_counts(), COMP_ORDER, "C"),
     lambda i: COMP_TITLES.get(i[2:], i[2:])),
    (order_layer(df["Year"].value_counts(), YEAR_ORDER, "Y"), lambda i: i[2:]),
    (order_layer(df["Engine"].value_counts(), ENGINE_ORDER, "E"), lambda i: i[2:]),
    (order_layer(df["MSK"].value_counts(), MSK_ORDER, "M"), lambda i: i[2:]),
    (order_layer(df["LDM"].value_counts(), LDM_ORDER, "L"), lambda i: i[2:]),
]
layer_ids = [ids for ids, _ in layer_raw]
layer_titles = ["Competition origin", "Years", "Physics Engine",
                "Musculoskeletal systems", "Learned Dynamics Model"]

out_links = [dict(source=f.source, target=f.target, value=int(f.value))
             for f in flows.itertuples()]
out_nodes = []
for li, (ids, title_fn) in enumerate(layer_raw):
    for i in ids:
        title = title_fn(i)
        out_nodes.append(dict(id=i, title=title, layer=li,
                              color=NODE_COLORS.get(title, DEFAULT_COLOR)))
for n in out_nodes:
    n["value"] = max(sum(l["value"] for l in out_links if l["source"] == n["id"]),
                     sum(l["value"] for l in out_links if l["target"] == n["id"]))

render_data = dict(nodes=out_nodes, links=out_links, layers=layer_ids,
                   layer_titles=layer_titles)
template = Path(__file__).with_name("sankey_template.html").read_text(encoding="utf-8")
html = template.replace("__DATA__", json.dumps(render_data, ensure_ascii=False))
(out_dir / "sankey_engine_msk.html").write_text(html, encoding="utf-8")
