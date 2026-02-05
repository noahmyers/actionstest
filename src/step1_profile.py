import os
import pandas as pd
import numpy as np

DATA_PATH = "data/je_samples.xlsx"
OUT_DIR = "outputs"

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

def read_data():
    df = pd.read_excel(DATA_PATH)
    return df

def basic_profile(df: pd.DataFrame) -> pd.DataFrame:
    profile = []
    n_rows = len(df)
    for col in df.columns:
        s = df[col]
        profile.append({
            "column": col,
            "dtype": str(s.dtype),
            "non_null": int(s.notna().sum()),
            "null": int(s.isna().sum()),
            "null_pct": float(s.isna().mean()),
            "n_unique": int(s.nunique(dropna=True))
        })
    prof_df = pd.DataFrame(profile).sort_values("null_pct", ascending=False)
    return prof_df

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    # Make best effort: convert likely date columns if present
    for col in ["EntryDate", "EffectiveDate"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def assertion_checks(df: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):
    """
    Produces:
      1) entry_balance summary (per JEEntryKey)
      2) failed balance list
      3) duplicate candidates
    """
    required_cols = ["JEEntryKey", "Amount"]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c}")

    # 1) Balanced entry test: sum of Amount per entry should be ~0
    grp = df.groupby("JEEntryKey", dropna=False)["Amount"].sum().reset_index()
    grp.rename(columns={"Amount": "entry_amount_sum"}, inplace=True)

    # tolerance for floating math / rounding: adjust if needed
    tol = 0.005
    grp["is_balanced"] = grp["entry_amount_sum"].abs() <= tol

    failed = grp.loc[~grp["is_balanced"]].copy()
    failed.sort_values("entry_amount_sum", key=lambda s: s.abs(), ascending=False, inplace=True)

    # 2) Duplicate candidates (simple heuristic)
    dup_cols = [c for c in ["JEEntryKey", "GLAccountNumber", "Amount", "EntryDate", "EffectiveDate", "Description"] if c in df.columns]
    if dup_cols:
        dupes = df[df.duplicated(subset=dup_cols, keep=False)].copy()
    else:
        dupes = df.iloc[0:0].copy()  # empty

    return grp, failed, dupes

def overview_stats(df: pd.DataFrame) -> pd.DataFrame:
    out = {}

    out["rows"] = len(df)
    out["columns"] = df.shape[1]

    if "JEEntryKey" in df.columns:
        out["unique_JEEntryKey"] = df["JEEntryKey"].nunique(dropna=True)

    if "EntryDate" in df.columns:
        out["EntryDate_min"] = df["EntryDate"].min()
        out["EntryDate_max"] = df["EntryDate"].max()

    if "EffectiveDate" in df.columns:
        out["EffectiveDate_min"] = df["EffectiveDate"].min()
        out["EffectiveDate_max"] = df["EffectiveDate"].max()

    if "Amount" in df.columns:
        out["Amount_sum"] = df["Amount"].sum()
        out["Amount_abs_sum"] = df["Amount"].abs().sum()
        out["Amount_min"] = df["Amount"].min()
        out["Amount_max"] = df["Amount"].max()

    return pd.DataFrame([out])

def main():
    ensure_out_dir()
    df = read_data()
    df = parse_dates(df)

    # Outputs
    prof = basic_profile(df)
    overview = overview_stats(df)
    balance_summary, balance_failed, dupes = assertion_checks(df)

    # Write outputs
    overview.to_csv(f"{OUT_DIR}/overview_stats.csv", index=False)
    prof.to_csv(f"{OUT_DIR}/column_profile.csv", index=False)
    balance_summary.to_csv(f"{OUT_DIR}/entry_balance_summary.csv", index=False)
    balance_failed.to_csv(f"{OUT_DIR}/entry_balance_failed.csv", index=False)
    dupes.to_csv(f"{OUT_DIR}/duplicate_candidates.csv", index=False)

    print("Wrote outputs to /outputs:")
    print("- overview_stats.csv")
    print("- column_profile.csv")
    print("- entry_balance_summary.csv")
    print("- entry_balance_failed.csv")
    print("- duplicate_candidates.csv")

if __name__ == "__main__":
    main()
