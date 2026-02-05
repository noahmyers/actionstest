from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/je_samples.xlsx")
OUTPUT_DIR = Path("outputs")


def normalize_column_name(column: str) -> str:
    return "".join(ch for ch in column.lower() if ch.isalnum())


def find_column_contains(columns: list[str], token: str) -> str | None:
    token = token.lower()
    for column in columns:
        if token in column.lower():
            return column
    return None


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(DATA_PATH)

    overview = {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT_DIR / "dataset_overview.json").write_text(
        json.dumps(overview, indent=2), encoding="utf-8"
    )

    summary_rows = []
    for column in df.columns:
        series = df[column]
        missing_count = int(series.isna().sum())
        summary_rows.append(
            {
                "column": column,
                "dtype": str(series.dtype),
                "non_null_count": int(series.notna().sum()),
                "missing_count": missing_count,
                "missing_pct": float(series.isna().mean() * 100),
                "unique_count": int(series.nunique(dropna=True)),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUTPUT_DIR / "dataset_summary.csv", index=False)

    missing_df = summary_df[["column", "missing_count", "missing_pct"]]
    missing_df.to_csv(OUTPUT_DIR / "missing_values_report.csv", index=False)

    normalized_columns = [normalize_column_name(column) for column in df.columns]
    je_key_column = None
    if "jeentrykey" in normalized_columns:
        je_key_column = df.columns[normalized_columns.index("jeentrykey")]
    else:
        je_key_column = find_column_contains(list(df.columns), "jeentrykey")

    debit_column = None
    credit_column = None
    for column in df.columns:
        normalized = normalize_column_name(column)
        if "debit" in normalized and debit_column is None:
            debit_column = column
        if "credit" in normalized and credit_column is None:
            credit_column = column

    if je_key_column and debit_column and credit_column:
        debit_values = pd.to_numeric(df[debit_column], errors="coerce").fillna(0)
        credit_values = pd.to_numeric(df[credit_column], errors="coerce").fillna(0)

        balance_df = (
            pd.DataFrame(
                {
                    je_key_column: df[je_key_column],
                    "debit_value": debit_values,
                    "credit_value": credit_values,
                }
            )
            .groupby(je_key_column, dropna=False)
            .sum(numeric_only=True)
            .reset_index()
        )
        balance_df.rename(
            columns={
                "debit_value": "debit_total",
                "credit_value": "credit_total",
            },
            inplace=True,
        )
        balance_df["net_balance"] = balance_df["debit_total"] - balance_df[
            "credit_total"
        ]
        balance_df["is_balanced"] = balance_df["net_balance"].abs() < 0.01
        balance_df.to_csv(OUTPUT_DIR / "je_balance_check.csv", index=False)
    else:
        error_message = (
            "Missing required columns for JE balance check. "
            f"Found JEEntryKey={je_key_column}, debit={debit_column}, credit={credit_column}."
        )
        pd.DataFrame({"error": [error_message]}).to_csv(
            OUTPUT_DIR / "je_balance_check.csv", index=False
        )

    duplicate_df = df[df.duplicated(keep=False)]
    duplicate_df.to_csv(OUTPUT_DIR / "duplicate_rows.csv", index=False)


if __name__ == "__main__":
    main()
