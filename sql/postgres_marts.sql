DROP VIEW IF EXISTS mart_retention_actions;
DROP VIEW IF EXISTS mart_revenue_at_risk;
DROP VIEW IF EXISTS mart_segment_churn;
DROP VIEW IF EXISTS mart_churn_overview;
DROP VIEW IF EXISTS mart_data_quality_status;

CREATE VIEW mart_churn_overview AS
SELECT COUNT(DISTINCT customer_id) total_customers,
       AVG(churn_flag::double precision) overall_churn_rate,
       SUM(monthly_charges) total_monthly_revenue,
       AVG(monthly_charges) avg_monthly_charges
FROM fact_customer_churn;

CREATE VIEW mart_segment_churn AS
SELECT 'contract' segment_type, c.contract segment_value, COUNT(*) customers,
       AVG(f.churn_flag::double precision) churn_rate, AVG(f.monthly_charges) avg_monthly_charges
FROM fact_customer_churn f JOIN dim_contract c USING(contract_id) GROUP BY c.contract
UNION ALL
SELECT 'payment_method', p.payment_method, COUNT(*), AVG(f.churn_flag::double precision), AVG(f.monthly_charges)
FROM fact_customer_churn f JOIN dim_payment p USING(payment_id) GROUP BY p.payment_method
UNION ALL
SELECT 'internet_service', s.internet_service, COUNT(*), AVG(f.churn_flag::double precision), AVG(f.monthly_charges)
FROM fact_customer_churn f JOIN dim_service s USING(service_id) GROUP BY s.internet_service
UNION ALL
SELECT 'combined_risk_segment', c.contract || ' | ' || p.payment_method || ' | ' || s.internet_service,
       COUNT(*), AVG(f.churn_flag::double precision), AVG(f.monthly_charges)
FROM fact_customer_churn f JOIN dim_contract c USING(contract_id)
JOIN dim_payment p USING(payment_id) JOIN dim_service s USING(service_id)
GROUP BY c.contract, p.payment_method, s.internet_service HAVING COUNT(*) >= 20;

CREATE VIEW mart_revenue_at_risk AS
SELECT f.customer_id, sc.churn_probability, f.monthly_charges,
       sc.churn_probability * f.monthly_charges revenue_at_risk,
       c.contract, p.payment_method, svc.internet_service, sc.scored_at_utc
FROM scored_customer_churn sc JOIN fact_customer_churn f USING(customer_id)
JOIN dim_contract c USING(contract_id) JOIN dim_payment p USING(payment_id)
JOIN dim_service svc USING(service_id);

CREATE VIEW mart_retention_actions AS
SELECT r.*,
 ROUND((100.0 * revenue_at_risk / MAX(monthly_charges) OVER ())::numeric, 2) retention_priority_score,
 CASE WHEN 100.0 * revenue_at_risk / MAX(monthly_charges) OVER () >= 60 THEN 'P1'
      WHEN 100.0 * revenue_at_risk / MAX(monthly_charges) OVER () >= 30 THEN 'P2' ELSE 'P3' END retention_priority,
 revenue_at_risk * 0.20 estimated_saved_revenue,
 CASE WHEN churn_probability >= .7 THEN 'High Risk' WHEN churn_probability >= .4 THEN 'Medium Risk' ELSE 'Low Risk' END risk_level,
 CASE WHEN churn_probability >= .7 AND contract='Month-to-month' THEN 'Offer long-term contract discount'
      WHEN churn_probability >= .7 THEN 'Priority outreach and personalized retention offer'
      WHEN churn_probability >= .4 THEN 'Proactive service check-in' ELSE 'Normal monitoring' END recommended_action
FROM mart_revenue_at_risk r;

CREATE VIEW mart_data_quality_status AS
WITH latest AS (SELECT * FROM meta_pipeline_runs ORDER BY completed_at_utc DESC LIMIT 1),
counts AS (SELECT (SELECT COUNT(*) FROM bronze_raw_customer_churn) raw_rows,
                  (SELECT COUNT(*) FROM silver_clean_customers) silver_rows,
                  (SELECT COUNT(*) FROM fact_customer_churn) fact_rows)
SELECT l.run_id, l.status pipeline_status, l.completed_at_utc, c.*,
       c.silver_rows-c.fact_rows reconciliation_variance,
       COUNT(*) FILTER (WHERE q.passed = false) failed_quality_checks,
       BOOL_AND(q.passed) FILTER (WHERE q.check_name='require_unique_key') customer_unique_passed,
       BOOL_AND(q.passed) FILTER (WHERE q.check_name='require_non_null') required_null_check_passed,
       BOOL_AND(q.passed) FILTER (WHERE q.check_name='fact_dimension_referential_integrity') referential_integrity_passed
FROM latest l CROSS JOIN counts c LEFT JOIN meta_data_quality_results q ON q.run_id=l.run_id
GROUP BY l.run_id,l.status,l.completed_at_utc,c.raw_rows,c.silver_rows,c.fact_rows;
