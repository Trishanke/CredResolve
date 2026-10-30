# Submission package

This folder contains the analysis notebook, SQL, dashboard, executive memo, data quality report, driver assessment, and production architecture. Raw inputs remain unchanged.

## Rebuild

From repository root, run with Python and pandas installed:

```powershell
python scripts/preprocess_collections.py
python scripts/build_assignment_submission.py
python scripts/render_dashboard.py
```

The first step writes conservative cleaned staging tables to `output/preprocessed/` and exact-row quarantine. The second creates golden accounts, current borrower/agent snapshots, canonical payments, monthly and account-month facts, segment summaries, and memo inputs. The third writes the static dashboard and data quality report.

## Interpretation

The dataset is synthetic and covers Jan 1-Aug 8, 2026. It supports a descriptive recorded-cash analysis, but not a year-long causal improvement or reliable ₹10 Cr ROI. See `driver_assessment.md`, `docs/metric_and_data_contract.md`, `docs/counterfactual_and_experiment.md`, and `docs/production_design.md` before reusing the metrics. SQL is written for DuckDB and uses the generated golden tables.

## Data handling

The source dataset and row-level generated exports are excluded from Git. Run the preprocessing and build scripts to recreate them locally from the assignment data. The aggregated monthly and segment summaries in this folder are included for review.
