# Customer Churn Analytics Warehouse and BI Dashboard

An end-to-end analytics engineering project that turns the Telco Customer Churn dataset into a tested retention decision system.

## Overview

This project helps a retention team identify where churn is concentrated, estimate the monthly revenue exposed to churn, prioritize customers for intervention, and verify that the supporting data passed quality checks.

The solution combines a reproducible Python pipeline, dimensional warehouse, governed SQL marts, churn-risk scoring, Streamlit application, and a five-page Power BI dashboard. It is designed as a portfolio project for BI Engineer, Analytics Engineer, Data Quality Engineer, Junior Data Engineer, and Data Analyst roles.

## Business Questions

1. What is the overall customer churn rate?
2. Which customer segments have the greatest churn exposure?
3. How much monthly revenue is at risk?
4. Which customers should receive retention offers first?
5. Did the data pipeline pass its quality gates before dashboard publication?

## Key Results

| Metric | Result |
|---|---:|
| Source customers | 7,043 |
| Observed churn rate | 26.54% |
| Total monthly revenue | $456,116.60 |
| Customers in scored population | 1,409 |
| High-risk customers | 350 |
| P1 retention customers | 139 |
| Probability-weighted monthly revenue at risk | $42,202.51 |
| Estimated monthly revenue saved at 20% success | $8,440.50 |
| Power BI-ready marts | 5 |
| Automated tests | 8 passing |

The warehouse covers all 7,043 source customers. Probability-based metrics use the 1,409-customer scored artifact in `results/risk_table_with_recommendations.csv`.

Key findings:

- Month-to-month contracts account for $34,486.53 of estimated revenue at risk.
- Electronic-check customers account for $23,448.95 of estimated revenue at risk.
- Fiber-optic customers account for $32,949.19 of estimated revenue at risk.
- The highest-churn combined segment is `Month-to-month | Electronic check | Fiber optic`, with a 60.37% churn rate.

Metric definitions and interpretation rules are documented in [Business Metrics](docs/BUSINESS_METRICS.md).

## Dashboard Preview

### Executive Overview

![Executive Overview](docs/screenshots/powerbi_executive_overview.png)

### Churned Customer Analysis

![Churned Customer Analysis](docs/screenshots/powerbi_churned_customer_analysis.png)

### Revenue at Risk

![Revenue at Risk](docs/screenshots/powerbi_revenue_at_risk.png)

### Retention Action Queue

![Retention Action Queue](docs/screenshots/powerbi_retention_action_queue.png)

### Data Quality Monitor

![Data Quality Monitor](docs/screenshots/powerbi_data_quality_monitor.png)

See the [Power BI Dashboard Guide](docs/POWERBI_DASHBOARD_GUIDE.md) for measures, field mappings, filters, and visual specifications.

## Architecture

```text
Raw Telco CSV
    ↓
Bronze source snapshot
    ↓
Cleaning, feature engineering, and quality gates
    ↓
Silver customers
    ↓
Dimensions + customer churn fact
    ↓
Gold aggregations + scored customers
    ↓
SQL marts
    ↓
Streamlit / Power BI exports / reports
```

SQLite is the default local warehouse. The pipeline publishes the final database only after critical validation checks pass.

| Layer | Purpose |
|---|---|
| Bronze | Preserve the raw source snapshot |
| Silver | Standardize and validate customer records |
| Dimensions and Fact | Provide a customer-level star schema |
| Gold | Create reusable business aggregations |
| Marts | Serve dashboard-ready metrics and action queues |
| Audit | Preserve pipeline runs and quality-check evidence |

Detailed schemas and data flow are available in [Warehouse Design](docs/WAREHOUSE_DESIGN.md).

## Tech Stack

- **Data pipeline:** Python, pandas
- **Machine learning:** scikit-learn, XGBoost
- **Warehouse and marts:** SQL, SQLAlchemy, SQLite
- **Visualization:** Power BI, Streamlit
- **Quality and CI:** pytest, GitHub Actions
- **Optional extensions:** PostgreSQL, Docker, Airflow, PySpark

## Repository Structure

```text
customer-churn-prediction/
├── .github/workflows/       # Continuous integration
├── dags/                    # Optional Airflow workflow
├── dashboard/               # Streamlit application
├── data/raw/                # Source Telco dataset
├── docs/                    # Design, metrics, quality, and Power BI guides
├── notebooks/               # EDA and model-training notebooks
├── reports/                 # Business report and figures
├── results/                 # Selected model and scoring artifacts
├── scripts/                 # Pipeline and export entry points
├── spark/                   # Optional PySpark transformations
├── sql/                     # Warehouse schema and SQL marts
├── src/                     # Cleaning, training, scoring, and warehouse logic
├── tests/                   # Automated tests
├── docker-compose.yml       # Optional PostgreSQL stack
└── requirements.txt
```

Selected committed outputs:

- `results/model_results.csv` — model comparison
- `results/threshold_results.csv` — threshold evaluation
- `results/risk_table_with_recommendations.csv` — complete scored population
- `results/top_30_high_risk_customers.csv` — compact portfolio sample

Generated databases and exports are intentionally ignored because the scripts can rebuild them.

## Quick Start

### 1. Create and activate an environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

### 2. Run the tests

```bash
pytest -q
```

### 3. Build the SQLite warehouse and marts

```bash
python scripts/build_churn_warehouse.py
```

The generated database is written to:

```text
data/warehouse/customer_churn_warehouse.sqlite
```

### 4. Launch the Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501`.

### 5. Export the Power BI source files

```bash
python scripts/export_powerbi_data.py
```

The five mart CSVs are generated in `results/powerbi_exports/`.

## Power BI Dashboard

The dashboard contains five pages:

1. **Executive Overview** — headline churn, revenue, risk, and priority KPIs
2. **Churned Customer Analysis** — segment size, churn rate, and estimated churn volume
3. **Revenue at Risk** — exposure by contract, payment method, service, and customer
4. **Retention Action Queue** — prioritized customer contacts and recommended actions
5. **Data Quality Monitor** — pipeline status, reconciliation, and validation evidence

Regenerate the source marts before refreshing Power BI:

```bash
python scripts/build_churn_warehouse.py
python scripts/export_powerbi_data.py
```

Construction guidance and DAX measures are in [Power BI Dashboard Guide](docs/POWERBI_DASHBOARD_GUIDE.md).

## Data Quality

Critical validation is built into the publication workflow. Checks cover:

- required columns and non-null business fields;
- unique customer identifiers;
- valid churn, tenure, and charge values;
- Silver-to-Fact row reconciliation;
- dimension referential integrity;
- valid Gold-table churn rates;
- persisted run-level and check-level audit evidence.

The latest verified build shows:

```text
Pipeline status: Passed
Raw rows: 7,043
Silver rows: 7,043
Fact rows: 7,043
Failed quality checks: 0
Reconciliation variance: 0
```

See [Data Quality Monitoring](docs/DATA_QUALITY_MONITORING.md) for implementation details and failure interpretation.

## Tests

The pytest suite validates data cleaning, warehouse construction, row reconciliation, audit persistence, mart creation, and expected business metrics.

```bash
pytest -q
```

GitHub Actions runs the test suite on pushes and pull requests.

## Optional Extensions

The main project runs locally with Python and SQLite. Optional portfolio extensions are kept brief here:

- PostgreSQL and Docker Compose provide a multi-service deployment path.
- Airflow provides scheduled pipeline orchestration.
- PySpark reproduces selected Gold aggregations with distributed DataFrames.

These components are not required for the quick start. Their production boundaries and next steps are summarized in [Production Readiness](docs/PRODUCTION_READINESS.md).

## Portfolio Value

This repository demonstrates a complete, business-oriented analytics workflow:

```text
raw data → trusted warehouse → governed marts → dashboard → retention action queue
```

It provides evidence of Python, SQL, dimensional modeling, machine-learning scoring, data-quality controls, BI development, automated testing, and business interpretation—while keeping the default workflow reproducible on a local machine.

Additional documentation is indexed in [docs/README.md](docs/README.md), and a Chinese portfolio summary is available in [PROJECT_PORTFOLIO_CN.md](docs/PROJECT_PORTFOLIO_CN.md).
