# Production Readiness Review

This document explains what parts of the project are production-style, what remains portfolio-level, and what should be improved before applying the design to a real business environment.

---

## Current readiness summary

| Area | Status | Evidence |
|---|---|---|
| Reproducible local pipeline | Ready for portfolio | `scripts/build_churn_warehouse.py` rebuilds the SQLite warehouse and marts |
| Automated tests | Ready for portfolio | `pytest -q` returns 8 passed |
| Data quality gates | Strong portfolio implementation | Implemented in `src/data_quality.py` and surfaced in `mart_data_quality_status` |
| Warehouse modeling | Strong portfolio implementation | Bronze, Silver, dimensions, fact, Gold, marts, audit tables |
| Power BI output | Ready for portfolio | `scripts/export_powerbi_data.py` exports five mart CSVs |
| Streamlit dashboard | Ready for local demo | `dashboard/app.py` reads SQLite or PostgreSQL |
| Docker/PostgreSQL path | Good local production-style demo | `docker-compose.yml` starts database, pipeline, and dashboard |
| Airflow orchestration | Demonstration-level | DAG exists but not required for local quick start |
| PySpark path | Demonstration-level | Spark script reproduces Gold segment tables |
| Full enterprise deployment | Not yet production | Needs cloud storage, secrets, monitoring, scheduled scoring, authentication, and campaign tracking |

---

## Verified local run

Commands executed from the project root:

```bash
pytest -q
python scripts/build_churn_warehouse.py
python scripts/apply_sql_marts.py
python scripts/export_powerbi_data.py
```

Expected test result:

```text
8 passed
```

Expected warehouse/mart counts:

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

---

## Strengths

### 1. Clear analytics-engineering flow

The project is not only a machine-learning notebook. It has a full data-to-decision flow:

```text
raw data → cleaned data → warehouse → marts → BI dashboard → retention queue
```

### 2. Data-quality checks are implemented, not only described

Quality checks are executable and block publication when they fail.

Examples:

- required columns;
- unique customer IDs;
- non-null required fields;
- valid churn target;
- numeric ranges;
- fact/Silver reconciliation;
- fact/dimension referential integrity;
- Gold churn-rate ranges.

### 3. Dashboard reads governed marts

The Power BI dashboard uses exported SQL mart CSVs rather than raw data. This is a stronger BI design because the KPI definitions are controlled in SQL.

### 4. Customer actions are operationalized

`mart_retention_actions` converts churn probability and revenue exposure into:

```text
risk_level
retention_priority
retention_priority_score
estimated_saved_revenue
recommended_action
```

This makes the project closer to a decision-support system.

### 5. Multiple execution modes are available

The project supports:

- local Python + SQLite;
- Streamlit local dashboard;
- Power BI CSV export;
- Docker Compose with PostgreSQL;
- optional Airflow DAG;
- optional PySpark Gold transformation;
- Google Colab helper script.

---

## Current limitations

### 1. Static public dataset

The source data is a static Telco CSV. It does not include event dates, campaign history, customer interactions, product usage logs, or real retention outcomes.

### 2. Scored population is a subset

The full warehouse contains 7,043 customers, but the committed scored artifact contains 1,409 rows. Therefore, `mart_revenue_at_risk` and `mart_retention_actions` cover the scored subset only.

### 3. Model scoring is not yet a scheduled production task

The project includes model-training and scoring utilities, but the committed pipeline loads an existing scored artifact:

```text
results/risk_table_with_recommendations.csv
```

A production version should retrain or score customers on a schedule and store model version metadata.

### 4. No model registry or drift monitoring

There is no model registry, feature drift monitor, score distribution monitor, or calibration report.

### 5. No campaign feedback loop

The current `estimated_saved_revenue` uses a planning assumption of 20% success. Real deployment should record:

```text
campaign assignment
control group
accepted offer
actual retained revenue
intervention cost
net uplift
```

### 6. No security or access control

The local Streamlit dashboard does not implement authentication, authorization, or row-level access controls.

---

## Recommended production improvements

### Priority 1: automate scoring

Add a scheduled scoring step that creates a governed table with:

```text
customer_id
model_version
score_version
churn_probability
scored_at_utc
threshold_high
threshold_medium
```

### Priority 2: add model monitoring

Track:

```text
score distribution
high-risk share
feature drift
prediction calibration
actual churn outcome by score band
```

### Priority 3: add campaign outcome tables

Suggested tables:

```text
fact_retention_campaign
fact_customer_intervention
dim_campaign
dim_offer
```

### Priority 4: move storage to production services

Potential stack:

```text
cloud object storage → warehouse/lakehouse → scheduled ETL → BI semantic model → dashboard refresh
```

### Priority 5: improve data governance

Add:

- secrets management;
- environment-specific configuration;
- data freshness SLA;
- access control;
- PII-handling policy;
- dashboard ownership;
- incident runbook.

---

## GitHub readiness checklist

Before pushing:

```text
□ README explains actual implementation and commands
□ docs/ folder is consistent with actual mart columns
□ Power BI screenshots are included in docs/screenshots/
□ Generated SQLite databases are not committed
□ Generated mart exports are not committed
□ __MACOSX and .DS_Store files are removed
□ pytest -q passes
□ scripts/build_churn_warehouse.py runs successfully
□ scripts/export_powerbi_data.py runs successfully
□ README does not claim unsupported functionality
```

---

## Interview positioning

Recommended description:

```text
This project is a customer churn analytics engineering and BI decision-support project. It builds a reproducible data pipeline from a raw Telco churn CSV into a validated SQLite warehouse, SQL marts, Power BI exports, and a customer-level retention action queue. It demonstrates Python, SQL, data-quality checks, warehouse modeling, dashboard design, and business metric interpretation.
```

Avoid positioning it as only a machine-learning project. The strongest part is the analytics pipeline and business decision layer.
