# Production Architecture

This project is a portfolio-scale implementation, but its structure follows production-style analytics engineering patterns: reproducible pipelines, data-quality gates, warehouse layers, SQL marts, BI outputs, dashboard application, orchestration, containerization, and optional scalable transformation.

---

## Architecture overview

```text
Raw CSV source
    ↓
Python cleaning and feature engineering
    ↓
SQLite local warehouse
    ↓
Data quality gates and audit metadata
    ↓
SQL marts
    ↓
Power BI exports + Streamlit dashboard
```

Optional execution paths:

```text
Airflow DAG → scheduled warehouse build and verification
Docker Compose → PostgreSQL + pipeline + Streamlit dashboard
PySpark → distributed Gold-table transformation demonstration
Colab helper → notebook-friendly project execution
```

---

## Local SQLite architecture

The default execution path is local SQLite because it is lightweight and reproducible.

Commands:

```bash
python scripts/build_churn_warehouse.py
python scripts/export_powerbi_data.py
streamlit run dashboard/app.py
```

Main outputs:

```text
data/warehouse/customer_churn_warehouse.sqlite
results/mart_exports/*.csv
results/powerbi_exports/*.csv
```

These generated artifacts are ignored by Git.

---

## Pipeline stages

### 1. Ingestion

Input:

```text
data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv
```

Loaded by:

```text
src/warehouse_builder.py::load_raw_data
```

Stored as:

```text
bronze_raw_customer_churn
```

### 2. Cleaning and feature engineering

Implemented in:

```text
src/data_cleaning.py
src/feature_engineering.py
```

Output:

```text
silver_clean_customers
```

### 3. Star-schema modeling

Implemented in:

```text
src/warehouse_builder.py
```

Output tables:

```text
dim_customer
dim_contract
dim_service
dim_payment
fact_customer_churn
```

### 4. Gold aggregations

Output tables:

```text
gold_churn_by_contract
gold_churn_by_payment
gold_high_risk_segments
```

### 5. Scored customer loading

Implemented in:

```text
scripts/apply_sql_marts.py::load_scored_customers
```

Input:

```text
results/risk_table_with_recommendations.csv
```

Output table:

```text
scored_customer_churn
```

### 6. SQL marts

Implemented in:

```text
sql/marts/
```

Dashboard-facing views:

```text
mart_churn_overview
mart_segment_churn
mart_revenue_at_risk
mart_retention_actions
mart_data_quality_status
```

---

## Data quality architecture

Quality checks run before publication.

If checks fail:

```text
pipeline raises an error → final SQLite warehouse is not promoted
```

If checks pass:

```text
temporary SQLite database → atomically promoted to customer_churn_warehouse.sqlite
```

Audit outputs:

```text
meta_pipeline_runs
meta_data_quality_results
mart_data_quality_status
```

---

## Streamlit dashboard architecture

Application:

```text
dashboard/app.py
```

The app supports two database modes:

| Mode | Behavior |
|---|---|
| SQLite | Reads `data/warehouse/customer_churn_warehouse.sqlite` |
| PostgreSQL | Reads from `DATABASE_URL` if the environment variable is set |

Run locally:

```bash
streamlit run dashboard/app.py
```

The dashboard uses SQL queries against the warehouse/mart layer rather than the raw CSV.

---

## Power BI architecture

Power BI uses flat CSV extracts generated from the SQL marts.

Command:

```bash
python scripts/export_powerbi_data.py
```

Output:

```text
results/powerbi_exports/
```

Power BI import files:

```text
mart_churn_overview.csv
mart_segment_churn.csv
mart_revenue_at_risk.csv
mart_retention_actions.csv
mart_data_quality_status.csv
```

This keeps dashboard logic separated from the raw source file and makes the dashboard depend on governed marts.

---

## Docker Compose architecture

The Docker Compose path provides a PostgreSQL-backed version of the workflow.

Command:

```bash
docker compose up --build
```

Services:

| Service | Purpose |
|---|---|
| `postgres` | PostgreSQL database |
| `pipeline` | Loads warehouse tables and PostgreSQL marts |
| `dashboard` | Runs Streamlit dashboard against PostgreSQL |

Service dependency order:

```text
postgres healthy → pipeline completed successfully → dashboard starts
```

The PostgreSQL volume is named:

```text
postgres_data
```

Stop services:

```bash
docker compose down
```

Remove volume:

```bash
docker compose down -v
```

---

## Airflow architecture

Optional DAG:

```text
dags/customer_churn_warehouse_dag.py
```

Schedule:

```text
0 2 * * *
```

DAG tasks:

1. validate source CSV;
2. build warehouse;
3. apply SQL marts;
4. verify warehouse quality checks.

Environment variables:

| Variable | Purpose |
|---|---|
| `CHURN_PROJECT_ROOT` | Project root path |
| `CHURN_RAW_CSV` | Source CSV path |
| `CHURN_WAREHOUSE_DB` | SQLite warehouse output path |
| `CHURN_RISK_CSV` | Scored customer artifact path |

Airflow is optional and is not installed with the base requirements.

---

## PySpark architecture

Optional Spark script:

```text
spark/build_churn_gold_tables_pyspark.py
```

Purpose:

```text
Reproduce Gold segment tables with Spark DataFrames.
```

Outputs:

```text
results/spark_gold/
```

The Spark path is supplemental. The default local workflow remains Python + SQLite.

---

## CI architecture

GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

Current CI behavior:

1. checks out the repository;
2. sets up Python 3.11;
3. installs core dependencies;
4. runs `pytest -q`.

Local expected result:

```text
8 passed
```

---

## Deployment limitations

This is not a full production system yet. Current limitations include:

- source data is a static public CSV;
- scored customer artifact is committed as a result file rather than produced by a scheduled model job;
- no secrets manager is used;
- no cloud object storage or managed warehouse is configured;
- no dashboard authentication is implemented;
- no real campaign outcome tracking is included;
- no automated Power BI refresh is configured.

The design is still useful for portfolio review because it demonstrates the architecture and implementation patterns needed for analytics engineering work.
