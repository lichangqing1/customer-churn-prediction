# Exploratory Notebooks

These notebooks are portfolio-facing exploration, not production pipeline code.
They are intentionally limited to two analytical use cases:

| Notebook | Purpose |
|---|---|
| `02_eda_business_analysis.ipynb` | Exploratory data analysis, segment comparisons, and business-facing churn visualizations |
| `03_model_training.ipynb` | Classifier experimentation, model comparison, threshold analysis, and feature interpretation |

Both notebooks read the raw Telco CSV and reuse functions from `src/`. Stored outputs
and execution counts are cleared before publication so stale exceptions, local paths,
and environment-specific results are not committed. Curated results are retained in
`results/` and `reports/figures/`.

## Production boundary

The notebooks are not imported by, or required for, any production workflow. The real
implementation lives in:

- `src/` — cleaning, features, quality checks, warehouse modeling, training, scoring,
  evaluation, and retention logic;
- `scripts/` — warehouse builds, SQL mart application, PostgreSQL loading, and BI exports;
- `dags/` — Airflow orchestration;
- `sql/` — SQLite and PostgreSQL analytical marts;
- `dashboard/` — the Streamlit decision-support application;
- `spark/` — distributed Gold-table transformations.

## Running a notebook

Start Jupyter from the repository root so `Path.cwd()` and `src` imports resolve:

```bash
jupyter notebook
```

Install the main project dependencies first. The model notebook also requires XGBoost,
which is included in `requirements.txt`.
