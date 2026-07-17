-- Consistent, unionable churn metrics for the primary business dimensions.
DROP VIEW IF EXISTS mart_segment_churn;
CREATE VIEW mart_segment_churn AS
SELECT 'contract' AS segment_type, c.contract AS segment_value,
       COUNT(*) AS customers, AVG(f.churn_flag * 1.0) AS churn_rate,
       AVG(f.monthly_charges) AS avg_monthly_charges
FROM fact_customer_churn f JOIN dim_contract c USING (contract_id)
GROUP BY c.contract
UNION ALL
SELECT 'payment_method', p.payment_method, COUNT(*), AVG(f.churn_flag * 1.0),
       AVG(f.monthly_charges)
FROM fact_customer_churn f JOIN dim_payment p USING (payment_id)
GROUP BY p.payment_method
UNION ALL
SELECT 'internet_service', s.internet_service, COUNT(*), AVG(f.churn_flag * 1.0),
       AVG(f.monthly_charges)
FROM fact_customer_churn f JOIN dim_service s USING (service_id)
GROUP BY s.internet_service
UNION ALL
SELECT 'combined_risk_segment',
       c.contract || ' | ' || p.payment_method || ' | ' || s.internet_service,
       COUNT(*), AVG(f.churn_flag * 1.0), AVG(f.monthly_charges)
FROM fact_customer_churn f
JOIN dim_contract c USING (contract_id)
JOIN dim_payment p USING (payment_id)
JOIN dim_service s USING (service_id)
GROUP BY c.contract, p.payment_method, s.internet_service
HAVING COUNT(*) >= 20;
