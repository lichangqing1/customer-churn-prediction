# Warehouse Design

This project implements a lightweight analytics warehouse in SQLite. The design is intentionally simple enough to run locally, but it follows common warehouse concepts: source preservation, cleaned Silver data, dimensions, fact table, Gold aggregations, SQL marts, and audit metadata.

---

## End-to-end flow

```text
Raw Telco CSV
    ↓
bronze_raw_customer_churn
    ↓
silver_clean_customers
    ↓
dim_customer + dim_contract + dim_service + dim_payment
    ↓
fact_customer_churn
    ↓
gold_churn_by_contract + gold_churn_by_payment + gold_high_risk_segments
    ↓
scored_customer_churn
    ↓
mart_churn_overview + mart_segment_churn + mart_revenue_at_risk + mart_retention_actions + mart_data_quality_status
```

The build is executed by:

```bash
python scripts/build_churn_warehouse.py
```

The output SQLite file is:

```text
data/warehouse/customer_churn_warehouse.sqlite
```

This file is generated at runtime and ignored by Git.

---

## Bronze layer

### `bronze_raw_customer_churn`

Purpose: preserve the raw Telco Customer Churn CSV exactly as ingested.

Source file:

```text
data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv
```

Expected row count:

```text
7,043
```

The Bronze table keeps original source column names such as `customerID`, `SeniorCitizen`, `MonthlyCharges`, `TotalCharges`, and `Churn`.

---

## Silver layer

### `silver_clean_customers`

Purpose: provide standardized, cleaned, feature-engineered customer records.

Main transformations are implemented in:

```text
src/data_cleaning.py
src/feature_engineering.py
src/warehouse_builder.py
```

Implemented transformations:

- standardize column names;
- rename Telco columns to snake_case;
- convert `total_charges` to numeric;
- encode `churn` as `churn_flag`;
- remove duplicate rows;
- add derived features such as average charge per tenure, high monthly charge flag, short tenure flag, long-term contract flag, tenure group, and monthly charge group.

Expected row count:

```text
7,043
```

---

## Dimension tables

### `dim_customer`

Grain: one row per customer.

Columns:

```text
customer_id, gender, senior_citizen, partner, dependents
```

Expected row count:

```text
7,043
```

### `dim_contract`

Grain: one row per contract type.

Columns:

```text
contract_id, contract
```

Expected row count:

```text
3
```

### `dim_service`

Grain: one row per observed service combination.

Columns:

```text
service_id, internet_service, phone_service, online_security, tech_support
```

Expected row count:

```text
13
```

### `dim_payment`

Grain: one row per payment method and paperless billing combination.

Columns:

```text
payment_id, payment_method, paperless_billing
```

Expected row count:

```text
8
```

---

## Fact table

### `fact_customer_churn`

Grain: one row per customer.

Main columns:

```text
customer_id
tenure
monthly_charges
total_charges
avg_charge_per_tenure
high_monthly_charge
short_tenure
is_long_term_contract
tenure_group
monthly_charge_group
churn_flag
contract_id
service_id
payment_id
```

Expected row count:

```text
7,043
```

Relationship logic:

```text
fact_customer_churn.customer_id → dim_customer.customer_id
fact_customer_churn.contract_id → dim_contract.contract_id
fact_customer_churn.service_id → dim_service.service_id
fact_customer_churn.payment_id → dim_payment.payment_id
```

SQLite foreign-key constraints are not physically declared in `to_sql`, but referential integrity is validated by the warehouse quality-check function.

---

## Gold tables

### `gold_churn_by_contract`

Grain: one row per contract type.

Columns:

```text
contract, customers, churn_rate, avg_monthly_charges
```

Expected row count:

```text
3
```

### `gold_churn_by_payment`

Grain: one row per payment method.

Columns:

```text
payment_method, customers, churn_rate, avg_monthly_charges
```

Expected row count:

```text
4
```

### `gold_high_risk_segments`

Grain: contract × payment method × internet service.

Columns:

```text
contract, payment_method, internet_service, customers, churn_rate, avg_monthly_charges
```

Filter rule:

```text
customers >= 20
```

Expected row count:

```text
35
```

---

## Scored customer table

### `scored_customer_churn`

This table is loaded by `scripts/apply_sql_marts.py` from:

```text
results/risk_table_with_recommendations.csv
```

Required input columns:

```text
customer_id, churn_risk_score
```

The script renames `churn_risk_score` to:

```text
churn_probability
```

It also adds:

```text
scored_at_utc
```

Expected row count:

```text
1,409
```

The scored population is a subset of the full 7,043-customer warehouse.

---

## SQL marts

SQL files live in:

```text
sql/marts/
```

They are applied in this order:

1. `mart_churn_overview.sql`
2. `mart_segment_churn.sql`
3. `mart_revenue_at_risk.sql`
4. `mart_retention_actions.sql`
5. `mart_data_quality_status.sql`

### `mart_churn_overview`

One-row executive summary.

Columns:

```text
total_customers
overall_churn_rate
total_monthly_revenue
avg_monthly_charges
```

### `mart_segment_churn`

Segment-level churn view.

Columns:

```text
segment_type
segment_value
customers
churn_rate
avg_monthly_charges
```

Expected row count:

```text
45
```

Important: this mart does not contain `churned_customers`.

### `mart_revenue_at_risk`

Customer-level revenue exposure view.

Columns:

```text
customer_id
churn_probability
monthly_charges
revenue_at_risk
contract
payment_method
internet_service
scored_at_utc
```

Expected row count:

```text
1,409
```

### `mart_retention_actions`

Customer-level action queue.

Columns:

```text
customer_id
churn_probability
monthly_charges
revenue_at_risk
contract
payment_method
internet_service
scored_at_utc
retention_priority_score
retention_priority
estimated_saved_revenue
risk_level
recommended_action
```

Expected row count:

```text
1,409
```

### `mart_data_quality_status`

Latest data-quality and pipeline status view.

Columns:

```text
run_id
pipeline_status
completed_at_utc
raw_rows
silver_rows
fact_rows
reconciliation_variance
failed_quality_checks
customer_unique_passed
required_null_check_passed
referential_integrity_passed
```

Expected row count:

```text
1
```

---

## Audit tables

### `meta_pipeline_runs`

Stores the latest pipeline run status.

Columns:

```text
run_id, status, source_rows, fact_rows, completed_at_utc
```

### `meta_data_quality_results`

Stores check-level evidence.

Columns:

```text
check_name, passed, details, gate, run_id, checked_at_utc
```

Expected row count after a full build:

```text
12
```

---

## Generated exports

`python scripts/build_churn_warehouse.py` creates:

```text
results/warehouse_exports/gold_churn_by_contract.csv
results/warehouse_exports/gold_churn_by_payment.csv
results/warehouse_exports/gold_high_risk_segments.csv
results/mart_exports/*.csv
```

`python scripts/export_powerbi_data.py` creates:

```text
results/powerbi_exports/mart_churn_overview.csv
results/powerbi_exports/mart_segment_churn.csv
results/powerbi_exports/mart_revenue_at_risk.csv
results/powerbi_exports/mart_retention_actions.csv
results/powerbi_exports/mart_data_quality_status.csv
```

These outputs are intentionally ignored by Git because they are reproducible.

---

## Verification commands

Run tests:

```bash
pytest -q
```

Build warehouse and marts:

```bash
python scripts/build_churn_warehouse.py
```

Export Power BI files:

```bash
python scripts/export_powerbi_data.py
```
