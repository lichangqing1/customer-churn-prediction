# Business Metrics

This document defines the metrics used by the churn warehouse, SQL marts, Streamlit dashboard, and Power BI dashboard.

## Data scope

| Scope | Source | Row count |
|---|---|---:|
| Full customer warehouse | `fact_customer_churn` | 7,043 |
| Segment churn marts | `mart_segment_churn` | 45 segment rows |
| Scored customer population | `results/risk_table_with_recommendations.csv` loaded into `scored_customer_churn` | 1,409 |
| Revenue-at-risk mart | `mart_revenue_at_risk` | 1,409 |
| Retention-action mart | `mart_retention_actions` | 1,409 |

The full dataset is used for observed churn-rate and segment analysis. The scored population is used for churn probability, revenue at risk, and retention actions.

---

## Executive overview metrics

Source mart: `mart_churn_overview`

| Column | Formula | Meaning |
|---|---|---|
| `total_customers` | `COUNT(DISTINCT customer_id)` | Total customers in the warehouse snapshot |
| `overall_churn_rate` | `AVG(churn_flag)` | Observed churn rate in the raw Telco dataset |
| `total_monthly_revenue` | `SUM(monthly_charges)` | Total current monthly charges in the warehouse |
| `avg_monthly_charges` | `AVG(monthly_charges)` | Average monthly charge per customer |

Current expected values:

| Metric | Value |
|---|---:|
| Total customers | 7,043 |
| Overall churn rate | 26.54% |
| Total monthly revenue | 456,116.60 |
| Average monthly charge | 64.76 |

---

## Segment churn metrics

Source mart: `mart_segment_churn`

| Column | Meaning |
|---|---|
| `segment_type` | Type of segment: `contract`, `payment_method`, `internet_service`, or `combined_risk_segment` |
| `segment_value` | Segment label |
| `customers` | Number of customers in the segment |
| `churn_rate` | Observed churn rate in the segment |
| `avg_monthly_charges` | Average monthly charge in the segment |

Important: this mart does **not** include a physical `churned_customers` column. If needed for Power BI, create:

```text
Estimated Churned Customers = customers × churn_rate
```

Recommended Power BI DAX:

```DAX
Estimated Churned Customers =
SUMX(
    mart_segment_churn,
    mart_segment_churn[customers] * mart_segment_churn[churn_rate]
)
```

Use the `segment_type` slicer when analyzing this mart. Otherwise, the same customer can be counted across multiple segment types.

Key segment examples:

| Segment | Customers | Churn rate | Avg monthly charges |
|---|---:|---:|---:|
| Month-to-month | 3,875 | 42.71% | 66.40 |
| Electronic check | 2,365 | 45.29% | 76.26 |
| Fiber optic | 3,096 | 41.89% | 91.50 |
| Month-to-month \| Electronic check \| Fiber optic | 1,307 | 60.37% | 87.18 |

---

## Revenue-at-risk metrics

Source mart: `mart_revenue_at_risk`

| Column | Formula / source | Meaning |
|---|---|---|
| `customer_id` | From scored customer output | Customer identifier |
| `churn_probability` | `churn_risk_score` renamed during mart loading | Predicted probability of churn |
| `monthly_charges` | From `fact_customer_churn` | Customer monthly charge |
| `revenue_at_risk` | `churn_probability × monthly_charges` | Probability-weighted expected monthly exposure |
| `contract` | From `dim_contract` | Contract type |
| `payment_method` | From `dim_payment` | Payment behavior |
| `internet_service` | From `dim_service` | Internet service category |
| `scored_at_utc` | Set when the scored artifact is loaded | Score load timestamp |

Important interpretation:

```text
Revenue at Risk is an expected-value measure.
It is not a guarantee that the full amount will be lost.
```

Current expected value:

```text
Total revenue at risk ≈ 42,202.51
```

---

## Retention action metrics

Source mart: `mart_retention_actions`

This mart extends `mart_revenue_at_risk` with priority and action columns.

| Column | Formula / rule | Meaning |
|---|---|---|
| `retention_priority_score` | `ROUND(100 × revenue_at_risk / MAX(monthly_charges), 2)` | Relative priority score from 0 to 100 |
| `retention_priority` | P1/P2/P3 based on priority score | Operational action tier |
| `estimated_saved_revenue` | `revenue_at_risk × 0.20` | Planning estimate assuming 20% campaign success |
| `risk_level` | Based on churn probability | High, Medium, or Low Risk |
| `recommended_action` | Rule-based action | Suggested retention intervention |

Risk-level rules:

| Risk level | Rule |
|---|---|
| High Risk | `churn_probability >= 0.70` |
| Medium Risk | `0.40 <= churn_probability < 0.70` |
| Low Risk | `churn_probability < 0.40` |

Retention-priority rules:

| Priority | Rule |
|---|---|
| P1 | `retention_priority_score >= 60` |
| P2 | `30 <= retention_priority_score < 60` |
| P3 | `retention_priority_score < 30` |

Recommended-action rules implemented in SQL:

| Condition | Action |
|---|---|
| High risk and month-to-month | Offer long-term contract discount |
| Other high risk | Priority outreach and personalized retention offer |
| Medium risk | Proactive service check-in |
| Low risk | Normal monitoring |

Current expected distributions:

| Metric | Value |
|---|---:|
| High Risk customers | 350 |
| Medium Risk customers | 343 |
| Low Risk customers | 716 |
| P1 customers | 139 |
| P2 customers | 385 |
| P3 customers | 885 |
| Estimated saved revenue | ~8,440.50 |

---

## Data quality metrics

Source mart: `mart_data_quality_status`

| Column | Meaning |
|---|---|
| `run_id` | Pipeline run identifier |
| `pipeline_status` | Latest pipeline status |
| `completed_at_utc` | Latest completion timestamp |
| `raw_rows` | Rows in Bronze table |
| `silver_rows` | Rows in Silver table |
| `fact_rows` | Rows in Fact table |
| `reconciliation_variance` | `silver_rows - fact_rows` |
| `failed_quality_checks` | Count of failed checks |
| `customer_unique_passed` | 1 if customer uniqueness passed |
| `required_null_check_passed` | 1 if required non-null check passed |
| `referential_integrity_passed` | 1 if fact/dimension integrity passed |

Current expected values:

```text
pipeline_status = success
raw_rows = 7043
silver_rows = 7043
fact_rows = 7043
reconciliation_variance = 0
failed_quality_checks = 0
```

---

## Business interpretation

The project should not be interpreted as only a predictive model. The useful business layer is the connection between:

```text
segment churn pattern + predicted churn probability + monthly revenue + recommended action
```

The strongest current retention target is the combined segment:

```text
Month-to-month | Electronic check | Fiber optic
```

This group combines high churn rate, high customer count, and high monthly charges.
