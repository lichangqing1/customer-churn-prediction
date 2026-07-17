-- Latest auditable pipeline outcome and its check-level status.
DROP VIEW IF EXISTS mart_data_quality_status;
CREATE VIEW mart_data_quality_status AS
WITH latest AS (
    SELECT * FROM meta_pipeline_runs ORDER BY completed_at_utc DESC LIMIT 1
), layer_counts AS (
    SELECT
      (SELECT COUNT(*) FROM bronze_raw_customer_churn) AS raw_rows,
      (SELECT COUNT(*) FROM silver_clean_customers) AS silver_rows,
      (SELECT COUNT(*) FROM fact_customer_churn) AS fact_rows
)
SELECT
    l.run_id,
    l.status AS pipeline_status,
    l.completed_at_utc,
    c.raw_rows,
    c.silver_rows,
    c.fact_rows,
    c.silver_rows - c.fact_rows AS reconciliation_variance,
    SUM(CASE WHEN q.passed = 0 THEN 1 ELSE 0 END) AS failed_quality_checks,
    MAX(CASE WHEN q.check_name = 'require_unique_key' THEN q.passed END) AS customer_unique_passed,
    MAX(CASE WHEN q.check_name = 'require_non_null' THEN q.passed END) AS required_null_check_passed,
    MAX(CASE WHEN q.check_name = 'fact_dimension_referential_integrity' THEN q.passed END) AS referential_integrity_passed
FROM latest l
CROSS JOIN layer_counts c
LEFT JOIN meta_data_quality_results q ON q.run_id = l.run_id
GROUP BY l.run_id, l.status, l.completed_at_utc, c.raw_rows, c.silver_rows, c.fact_rows;
