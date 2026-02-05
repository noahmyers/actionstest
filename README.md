# actionstest

## Data contract check

This repository includes a GitHub Actions workflow that runs a data contract check against
`data/je_samples.xlsx` and publishes an `outputs/` artifact.

### What the check produces

The workflow generates the following files in the `outputs/` folder:

- `dataset_overview.json` – high-level dataset counts.
- `dataset_summary.csv` – per-column summary (types, missing counts, uniqueness).
- `missing_values_report.csv` – missing values per column.
- `je_balance_check.csv` – JE balance check grouped by `JEEntryKey`.
- `duplicate_rows.csv` – rows that appear more than once.

### Run it in GitHub

1. Go to the **Actions** tab.
2. Select **Data Contract Check**.
3. Click **Run workflow**.
4. After the run completes, download the **data-contract-outputs** artifact from the run summary.
