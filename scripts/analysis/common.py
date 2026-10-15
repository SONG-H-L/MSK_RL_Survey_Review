import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import config

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data" / config.DATA_FILE

POOL_LABEL = {"total": "All papers", "yes": "Competition-origin papers",
              "no": "Non-competition papers"}


def clean_str(s):
    return s.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()


def to_period(year):
    if year <= 2019:
        return config.PERIODS[0]
    if year <= 2022:
        return config.PERIODS[1]
    return config.PERIODS[2]


def load_combos(path=None):
    df = pd.read_excel(path or DATA, sheet_name=config.SHEET_COMBOS)
    df = df.rename(columns={config.COL_ENGINE: "Engine"})
    df["Engine"] = clean_str(df["Engine"]).str.replace(
        "mujoco", "MuJoCo", case=False, regex=False)
    df["MSK"] = clean_str(df[config.COL_MSK])
    df.loc[df["MSK"].str.lower() == "myoelbow", "MSK"] = "Myoelbow"
    df["Comp"] = clean_str(df[config.COL_COMP])
    df["Year"] = df[config.COL_YEARS].astype(int)
    df["LDM"] = df[config.COL_LDM].astype(object)
    df.loc[df["LDM"].isna(), "LDM"] = "N/A"
    df["LDM"] = clean_str(df["LDM"])
    return df


def load_studies(path=None):
    s1 = pd.read_excel(path or DATA, sheet_name=config.SHEET_STUDIES)
    s1 = s1[~s1[config.COL_ID].isin(config.DROP_IDS)].copy()
    s1["Year"] = s1[config.COL_YEARS].astype(int)
    s1["Period"] = pd.Categorical(s1["Year"].map(to_period),
                                  categories=config.PERIODS, ordered=True)
    s1["Pool"] = np.where(clean_str(s1[config.COL_COMP]) == "No", "No", "Yes")
    return s1


def load_tasks(path=None):
    s2 = pd.read_excel(path or DATA, sheet_name=config.SHEET_TASKS)
    em = pd.read_excel(path or DATA, sheet_name=config.SHEET_COMBOS)
    comp_map = em[[config.COL_ID, config.COL_COMP]].drop_duplicates(subset=config.COL_ID)
    if config.COL_COMP in s2.columns:
        s2 = s2.drop(columns=[config.COL_COMP])
    s2 = s2.merge(comp_map, on=config.COL_ID, how="left")
    s2 = s2[~s2[config.COL_ID].isin(config.DROP_IDS)].copy()
    s2["Pool"] = np.where(clean_str(s2[config.COL_COMP]) == "No", "No", "Yes")
    s2["Year"] = s2[config.COL_YEARS].astype(int)
    s2["Period"] = s2["Year"].map(to_period)
    s2["Task type"] = clean_str(s2[config.COL_TASK_TYPE])
    s2["Subcategory"] = clean_str(s2[config.COL_SUBCATEGORY])
    s2["TaskCat"] = (s2["Task type"] + " " + s2["Subcategory"]).str.strip()
    s2["Clearly"] = clean_str(s2[config.COL_CLEARLY])
    s2["DataRef"] = np.where(s2[config.COL_DATAREF].astype(str).str.strip() == "1.0",
                             "With data reference", "Without data reference")
    return s2


def pools_of(df):
    return {"total": df, "no": df[df["Pool"] == "No"], "yes": df[df["Pool"] == "Yes"]}


def cli(desc):
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--data", default=str(DATA))
    p.add_argument("--out", default="analysis_outputs")
    p.add_argument("--dpi", type=int, default=300)
    return p.parse_args()
