# CredResolve collections analysis

A reproducible data-forensics and collections-performance analysis for the Data Analyst assignment. The work includes conservative CSV preprocessing, payment identity reconciliation, monthly metrics, a one-screen dashboard, executive memo, quality report, SQL, analysis notebook, counterfactual plan, and production design.

## Dataset

The supplied dataset is intentionally excluded from this repository. It contains row-level identifiers and contact-like fields, and the analysis data are reproducible from the source inputs. To rebuild locally, place the assignment dataset in `collections_30k_dataset (1)/` at the repository root. The expected files and schema are listed in the assignment package's data dictionary.

## Rebuild

With Python and pandas installed, run from the repository root:

```powershell
python scripts/preprocess_collections.py
python scripts/build_assignment_submission.py
python scripts/render_dashboard.py
```

The scripts write generated staging and golden CSVs under the ignored `output/` folder. Aggregated outputs and the dashboard are tracked under `submission/`.

## Main deliverables

- `submission/executive_memo.md`
- `submission/dashboard/executive_dashboard.html`
- `submission/data_quality_report.md`
- `submission/driver_assessment.md`
- `submission/notebooks/collections_analysis.ipynb`
- `submission/sql/`
- `submission/docs/` (metric definitions, counterfactual, architecture, production design)

The available data cover Jan 1–Aug 8, 2026. Findings are descriptive; the source does not support a validated historical recovery rate, causal lift, or reliable ₹10 Cr ROI.
