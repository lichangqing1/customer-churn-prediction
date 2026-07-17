# Customer Churn Analytics Warehouse and BI Dashboard

A practical analytics-engineering project that turns the public Telco Customer Churn dataset into a tested customer-retention decision system. The implementation includes a reproducible data pipeline, SQLite analytics warehouse, SQL marts, data-quality gates, churn-risk scoring outputs, retention-action recommendations, Streamlit dashboard, Power BI-ready exports, optional Airflow scheduling, optional PostgreSQL deployment, and optional PySpark Gold-table transformation.

This repository is designed for portfolio review for roles such as **BI Engineer**, **Analytics Engineer**, **Data Quality Engineer**, **Junior Data Engineer**, **AI/Data Test Engineer**, and **Data Analyst**.

---

## Project outcomes

The project answers five business questions:

1. What is the overall customer churn rate?
2. Which customer segments have the highest churn exposure?
3. How much monthly revenue is at risk based on churn probability?
4. Which customers should be prioritized for retention actions?
5. Did the data pipeline pass quality checks before the dashboard was published?

The current verified local run produces:

| Output | Result |
|---|---:|
| Source customers | 7,043 |
| Overall observed churn rate | 26.54% |
| Total monthly revenue | 456,116.60 |
| Scored customers loaded into marts | 1,409 |
| Probability-weighted monthly revenue at risk | ~42,202.51 |
| High-risk customers in action queue | 350 |
| SQL marts exported for Power BI | 5 |
| Pytest result | 8 passed |

> Note: the warehouse contains all 7,043 customers. The revenue-at-risk and retention-action marts are based on the 1,409-customer scored artifact in `results/risk_table_with_recommendations.csv`.

---

## Key features

- **Bronze → Silver → Dimensions/Fact → Gold → Mart pipeline**
- **SQLite warehouse** for local reproducible analytics
- **PostgreSQL deployment path** through Docker Compose
- **Data quality gates** for required columns, unique customer IDs, non-null checks, numeric ranges, row reconciliation, referential integrity, and Gold-table churn-rate ranges
- **Atomic warehouse publication**: a failed validation blocks publication of the final SQLite database
- **SQL marts** for executive KPIs, segment analysis, revenue-at-risk, retention queue, and data-quality monitoring
- **Power BI export script** that creates five dashboard-ready CSV files
- **Streamlit dashboard** for interactive local decision support
- **ML scoring utilities** for churn probabilities, risk levels, revenue at risk, and retention recommendations
- **Airflow DAG** for scheduled execution
- **PySpark Gold-table script** to demonstrate a scalable transformation version
- **CI workflow** running the automated test suite on GitHub Actions

---

## Repository structure

```text
customer-churn-prediction/
├── .github/workflows/ci.yml
├── dags/customer_churn_warehouse_dag.py
├── dashboard/app.py
├── data/
│   └── raw/WA_Fn-UseC_-Telco-Customer-Churn.csv
├── docs/
│   ├── README.md
│   ├── BUSINESS_METRICS.md
│   ├── COLAB_EXECUTION.md
│   ├── DATA_QUALITY_MONITORING.md
│   ├── POWERBI_DASHBOARD_GUIDE.md
│   ├── PRODUCTION_ARCHITECTURE.md
│   ├── PRODUCTION_READINESS.md
│   ├── PROJECT_PORTFOLIO_CN.md
│   └── WAREHOUSE_DESIGN.md
├── notebooks/
│   ├── 02_eda_business_analysis.ipynb
│   ├── 03_model_training.ipynb
│   └── README.md
├── reports/
│   ├── business_insights_report.md
│   └── figures/
├── results/
│   ├── model_results.csv
│   ├── threshold_results.csv
│   ├── risk_table_with_recommendations.csv
│   └── high_risk_customers.csv
├── scripts/
│   ├── build_churn_warehouse.py
│   ├── apply_sql_marts.py
│   ├── export_powerbi_data.py
│   ├── load_postgres_warehouse.py
│   └── run_colab.py
├── spark/build_churn_gold_tables_pyspark.py
├── sql/
│   ├── warehouse_schema.sql
│   ├── postgres_marts.sql
│   └── marts/
├── src/
│   ├── data_cleaning.py
│   ├── data_quality.py
│   ├── feature_engineering.py
│   ├── model_training.py
│   ├── scoring.py
│   ├── retention_recommendations.py
│   └── warehouse_builder.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

---

## Quick start: local Python workflow

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows PowerShell
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Run tests

```bash
pytest -q
```

Expected result:

```text
8 passed
```

### 4. Build the SQLite warehouse and SQL marts

```bash
python scripts/build_churn_warehouse.py
```

Expected tables and row counts:

```text
bronze_raw_customer_churn: 7043
silver_clean_customers: 7043
dim_customer: 7043
dim_contract: 3
dim_service: 13
dim_payment: 8
fact_customer_churn: 7043
gold_churn_by_contract: 3
gold_churn_by_payment: 4
gold_high_risk_segments: 35
mart_churn_overview: 1
mart_segment_churn: 45
mart_revenue_at_risk: 1409
mart_retention_actions: 1409
mart_data_quality_status: 1
```

The generated SQLite database is created at:

```text
data/warehouse/customer_churn_warehouse.sqlite
```

This file is intentionally ignored by Git because it is reproducible.

### 5. Export Power BI CSV files

```bash
python scripts/export_powerbi_data.py
```

This creates:

```text
results/powerbi_exports/mart_churn_overview.csv
results/powerbi_exports/mart_segment_churn.csv
results/powerbi_exports/mart_revenue_at_risk.csv
results/powerbi_exports/mart_retention_actions.csv
results/powerbi_exports/mart_data_quality_status.csv
```

These generated CSV files are also ignored by Git because they can be rebuilt.

### 6. Launch the Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

Then open:

```text
http://localhost:8501
```

---

## Pipeline architecture

```text
Raw Telco CSV
    ↓
Bronze raw source snapshot
    ↓
Cleaning + feature engineering + Silver data quality checks
    ↓
Silver clean customer table
    ↓
Dimension tables + customer-level churn fact table
    ↓
Gold aggregation tables
    ↓
Scored customer table loaded from model output
    ↓
SQL marts
    ↓
Streamlit dashboard / Power BI CSV exports / business reports
```

The base warehouse is created by `src/warehouse_builder.py` and executed through `scripts/build_churn_warehouse.py`.

The SQL marts are created from the files in `sql/marts/`:

| Mart | Grain | Purpose |
|---|---|---|
| `mart_churn_overview` | One row | Executive KPIs |
| `mart_segment_churn` | Segment level | Churn rate and customer count by segment |
| `mart_revenue_at_risk` | Scored customer level | Probability-weighted revenue exposure |
| `mart_retention_actions` | Scored customer level | Retention priority, risk level, and recommended action |
| `mart_data_quality_status` | Latest run | Pipeline health and quality-check status |

Important implementation detail: `mart_segment_churn` has these columns only:

```text
segment_type, segment_value, customers, churn_rate, avg_monthly_charges
```

It does **not** include a `churned_customers` column. If needed in Power BI, estimated churned customers should be calculated as:

```text
Estimated churned customers = customers × churn_rate
```

---

## Data warehouse design

| Layer | Tables | Description |
|---|---|---|
| Bronze | `bronze_raw_customer_churn` | Raw Telco CSV snapshot |
| Silver | `silver_clean_customers` | Cleaned, standardized, feature-engineered customer records |
| Dimensions | `dim_customer`, `dim_contract`, `dim_service`, `dim_payment` | Star-schema descriptive entities |
| Fact | `fact_customer_churn` | One customer row with churn flag, charges, tenure, and dimension keys |
| Gold | `gold_churn_by_contract`, `gold_churn_by_payment`, `gold_high_risk_segments` | Aggregated analytics tables |
| Score input | `scored_customer_churn` | Churn probabilities loaded from `results/risk_table_with_recommendations.csv` |
| Marts | `mart_*` views | Dashboard and Power BI output layer |
| Audit | `meta_pipeline_runs`, `meta_data_quality_results` | Pipeline run status and check-level evidence |

More details are available in [`docs/WAREHOUSE_DESIGN.md`](docs/WAREHOUSE_DESIGN.md).

---

## Data quality

The pipeline validates data before publishing analytics outputs.

Implemented checks include:

- required raw and Silver columns exist;
- `customer_id` is unique;
- required business fields are non-null;
- `churn_flag` contains only `0` and `1`;
- tenure and charge values are numeric and within valid ranges;
- Fact and Silver row counts reconcile;
- Fact rows have valid dimension references;
- Gold churn rates are between 0 and 1;
- mart-level status is published for dashboard monitoring.

The current verified `mart_data_quality_status` output is:

```text
pipeline_status: success
raw_rows: 7043
silver_rows: 7043
fact_rows: 7043
reconciliation_variance: 0
failed_quality_checks: 0
customer_unique_passed: 1
required_null_check_passed: 1
referential_integrity_passed: 1
```

See [`docs/DATA_QUALITY_MONITORING.md`](docs/DATA_QUALITY_MONITORING.md).

---

## Business metrics

Core metrics include:

```text
Observed churn rate = churned customers / total customers
Revenue at risk = churn probability × monthly charges
Estimated saved revenue = revenue at risk × 20%
Retention priority score = 100 × revenue_at_risk / max(monthly_charges)
```

Operational thresholds:

| Risk level | Rule |
|---|---|
| High Risk | `churn_probability >= 0.70` |
| Medium Risk | `0.40 <= churn_probability < 0.70` |
| Low Risk | `churn_probability < 0.40` |

Retention priorities:

| Priority | Rule |
|---|---|
| P1 | `retention_priority_score >= 60` |
| P2 | `30 <= retention_priority_score < 60` |
| P3 | `retention_priority_score < 30` |

See [`docs/BUSINESS_METRICS.md`](docs/BUSINESS_METRICS.md).

---

## Power BI dashboard

Power BI should use the files generated by:

```bash
python scripts/export_powerbi_data.py
```

Recommended Power BI pages:

1. **Executive Overview**
2. **Churned Customer Analysis**
3. **Revenue at Risk**
4. **Retention Action Queue**
5. **Data Quality Monitor**

Dashboard screenshots are included in `docs/screenshots/`:

```text
powerbi_executive_overview.png
powerbi_churned_customer_analysis.png
powerbi_revenue_at_risk.png
powerbi_retention_action_queue.png
powerbi_data_quality_monitor.png
```

Detailed construction guidance is available in [`docs/POWERBI_DASHBOARD_GUIDE.md`](docs/POWERBI_DASHBOARD_GUIDE.md).

### Dashboard preview

| Page | Screenshot |
|---|---|
| Executive Overview | ![Executive Overview](docs/screenshots/powerbi_executive_overview.png) |
| Churned Customer Analysis | ![Churned Customer Analysis](docs/screenshots/powerbi_churned_customer_analysis.png) |
| Revenue at Risk | ![Revenue at Risk](docs/screenshots/powerbi_revenue_at_risk.png) |
| Retention Action Queue | ![Retention Action Queue](docs/screenshots/powerbi_retention_action_queue.png) |
| Data Quality Monitor | ![Data Quality Monitor](docs/screenshots/powerbi_data_quality_monitor.png) |

---

## Streamlit dashboard

The Streamlit app in `dashboard/app.py` can read from either:

1. local SQLite database: `data/warehouse/customer_churn_warehouse.sqlite`; or
2. PostgreSQL when `DATABASE_URL` is set.

Main dashboard sections:

- Executive overview
- Priority segment analysis
- Segment churn performance
- Actionable customer queue
- Revenue-at-risk analysis
- Pipeline health and data-quality checks

Run locally:

```bash
python scripts/build_churn_warehouse.py
streamlit run dashboard/app.py
```

---

## Machine learning and scoring layer

The project includes classifier pipeline utilities in `src/model_training.py`:

- Logistic Regression
- Random Forest
- XGBoost

The committed `results/model_results.csv` currently reports Logistic Regression and Random Forest experiment results. The scoring layer uses probability outputs to create customer-level risk bands and revenue exposure.

Main scoring logic:

- `src/scoring.py`: validates probability outputs and assigns risk levels
- `src/retention_recommendations.py`: translates risk into retention actions
- `results/risk_table_with_recommendations.csv`: scored customer artifact used by SQL marts

The highest-risk operational queue is created in `mart_retention_actions`.

---

## Optional: Docker Compose with PostgreSQL

Run the production-style local stack:

```bash
docker compose up --build
```

This starts:

1. PostgreSQL database
2. pipeline container that loads the warehouse and PostgreSQL marts
3. Streamlit dashboard container

Open:

```text
http://localhost:8501
```

Stop without deleting the database volume:

```bash
docker compose down
```

Stop and delete the PostgreSQL volume:

```bash
docker compose down -v
```

See [`docs/PRODUCTION_ARCHITECTURE.md`](docs/PRODUCTION_ARCHITECTURE.md).

---

## Optional: Airflow DAG

The project includes an optional DAG at:

```text
dags/customer_churn_warehouse_dag.py
```

It validates the source file, builds the warehouse, applies marts, and verifies quality checks. Airflow is not required for the local quick start.

Install optional dependency:

```bash
python -m pip install -r requirements-airflow.txt
```

---

## Optional: PySpark Gold-table transformation

The Spark script reproduces the Gold segment tables using PySpark DataFrames:

```bash
python -m pip install -r requirements-spark.txt
python spark/build_churn_gold_tables_pyspark.py
```

Outputs are written to:

```text
results/spark_gold/
```

See [`spark/README.md`](spark/README.md).

---

## Google Colab execution

The project includes a Colab helper script:

```bash
python scripts/run_colab.py --install --test --dashboard
```

See [`docs/COLAB_EXECUTION.md`](docs/COLAB_EXECUTION.md).

---

## What is intentionally not committed

The following outputs are reproducible and ignored by Git:

```text
data/warehouse/*.sqlite
data/processed/*.csv
results/warehouse_exports/
results/mart_exports/
results/powerbi_exports/
results/spark_gold/
```

The repository keeps the raw dataset, selected result summaries, business report, dashboard screenshots, source code, tests, SQL files, and documentation.

---

## Portfolio value

This project demonstrates more than a basic churn classifier. It shows an end-to-end analytics workflow:

```text
raw data → trusted warehouse → governed marts → dashboard → action queue → data-quality monitoring
```

It is especially relevant for interviews where employers expect evidence of SQL, Python, BI modeling, data-quality thinking, dashboard design, and practical business interpretation.
