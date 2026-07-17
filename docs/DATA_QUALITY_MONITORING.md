# Data Quality Monitoring

This document describes the actual data-quality checks implemented in the customer churn project and how the results appear in the dashboard layer.

---

## Why this matters

A churn dashboard is only useful if stakeholders can trust the underlying data. This project therefore validates the data before publishing the warehouse and exposes a data-quality mart for monitoring.

The implementation is in:

```text
src/data_quality.py
src/warehouse_builder.py
sql/marts/mart_data_quality_status.sql
```

---

## Quality gates

The pipeline has two main quality gates:

| Gate | Stage | Purpose |
|---|---|---|
| Silver gate | After cleaning and feature engineering | Validate customer-level data before modeling or warehouse loading |
| Warehouse gate | After building dimensions, fact, and Gold tables | Validate the published warehouse structure and analytical outputs |

If a required quality check fails, the pipeline raises an error and does not publish the final warehouse.

---

## Silver data checks

Implemented by `run_clean_data_quality_checks(df)`.

| Check | Implementation | Purpose |
|---|---|---|
| Required columns | `require_columns` | Confirms key columns such as `customer_id`, `tenure`, `monthly_charges`, `total_charges`, `contract`, `payment_method`, `churn`, and `churn_flag` exist |
| Unique customer ID | `require_unique_key` | Confirms each `customer_id` appears once |
| Required non-null fields | `require_non_null` | Confirms required business fields are not null |
| Churn target domain | `require_values_in_set` | Confirms `churn_flag` contains only 0 or 1 |
| Tenure range | `require_numeric_range` | Confirms tenure is numeric and within the configured range |
| Monthly charge range | `require_numeric_range` | Confirms monthly charges are non-negative |
| Total charge range | `require_numeric_range` | Confirms total charges are non-negative |

---

## Warehouse checks

Implemented by `run_warehouse_quality_checks(db_path)`.

| Check name | Purpose |
|---|---|
| `warehouse_required_tables` | Confirms all required warehouse tables exist |
| `fact_silver_row_count` | Confirms Fact row count equals Silver row count |
| `fact_customer_unique` | Confirms one fact row per customer |
| `fact_dimension_referential_integrity` | Confirms fact rows match customer, contract, service, and payment dimensions |
| `gold_churn_rate_range` | Confirms Gold-table churn rates are between 0 and 1 |

---

## Atomic publication behavior

The warehouse builder writes to a temporary SQLite path first:

```text
customer_churn_warehouse.sqlite.tmp
```

Only after the checks pass does the script promote the temporary file to:

```text
data/warehouse/customer_churn_warehouse.sqlite
```

This protects the last good warehouse from being overwritten by a failed build.

---

## Audit tables

### `meta_data_quality_results`

Stores check-level evidence.

Columns:

```text
check_name
passed
details
gate
run_id
checked_at_utc
```

Expected row count after a full build:

```text
12
```

### `meta_pipeline_runs`

Stores the latest pipeline run status.

Columns:

```text
run_id
status
source_rows
fact_rows
completed_at_utc
```

---

## Data quality mart

The dashboard-facing quality mart is:

```text
mart_data_quality_status
```

Created by:

```text
sql/marts/mart_data_quality_status.sql
```

Columns:

| Column | Meaning |
|---|---|
| `run_id` | Latest pipeline run identifier |
| `pipeline_status` | Latest run status |
| `completed_at_utc` | Completion timestamp |
| `raw_rows` | Bronze row count |
| `silver_rows` | Silver row count |
| `fact_rows` | Fact row count |
| `reconciliation_variance` | `silver_rows - fact_rows` |
| `failed_quality_checks` | Number of failed checks |
| `customer_unique_passed` | 1 if uniqueness check passed |
| `required_null_check_passed` | 1 if required non-null check passed |
| `referential_integrity_passed` | 1 if fact/dimension integrity check passed |

Expected current values:

```text
pipeline_status = success
raw_rows = 7043
silver_rows = 7043
fact_rows = 7043
reconciliation_variance = 0
failed_quality_checks = 0
customer_unique_passed = 1
required_null_check_passed = 1
referential_integrity_passed = 1
```

---

## Data Quality Monitor dashboard page

Recommended Power BI visuals:

### KPI cards

- Data Quality Status
- Raw Rows
- Silver Rows
- Fact Rows
- Failed Checks
- Reconciliation Variance

### Row-count chart

Use a helper table to compare:

```text
Raw → Silver → Fact
```

All three should show:

```text
7,043
```

### Quality-check status chart

Use a disconnected helper table with check names:

```text
Customer uniqueness
Required null check
Referential integrity
Row reconciliation
Failed quality checks
```

Then map each label to a pass/fail measure.

### Detail table

Include:

```text
pipeline_status
raw_rows
silver_rows
fact_rows
reconciliation_variance
failed_quality_checks
customer_unique_passed
required_null_check_passed
referential_integrity_passed
```

---

## Recommended Power BI DAX

### Data Quality Status

```DAX
Data Quality Status =
IF(
    [Failed Quality Checks] = 0
        && [Reconciliation Variance] = 0,
    "Passed",
    "Failed"
)
```

### Row Reconciliation Passed

```DAX
Row Reconciliation Passed =
IF(
    [Raw Rows] = [Silver Rows]
        && [Silver Rows] = [Fact Rows],
    "Passed",
    "Failed"
)
```

### Quality Checks helper table

Use `Modeling → New table`, not SQL:

```DAX
Quality Checks =
UNION(
    ROW("Check Name", "Customer uniqueness"),
    ROW("Check Name", "Required null check"),
    ROW("Check Name", "Referential integrity"),
    ROW("Check Name", "Row reconciliation"),
    ROW("Check Name", "Failed quality checks")
)
```

Do not create a relationship between this helper table and `mart_data_quality_status`; it is a disconnected display table.

---

## Interpreting failures

| Symptom | Possible cause | Action |
|---|---|---|
| `failed_quality_checks > 0` | One or more checks failed | Read `meta_data_quality_results` for details |
| `reconciliation_variance != 0` | Fact and Silver row counts do not match | Check merge logic in `build_fact_table` |
| `referential_integrity_passed = 0` | Fact rows do not match dimensions | Check dimension key generation and joins |
| `customer_unique_passed = 0` | Duplicate customer IDs | Deduplicate or investigate source issues |
| `required_null_check_passed = 0` | Required fields have missing values | Fix cleaning or imputation logic |

---

## Portfolio interpretation

This page demonstrates data-quality thinking. It shows that the dashboard is not only visually useful, but also backed by validation rules and auditable pipeline evidence.
