-- Requires scored_customer_churn to be loaded from the model scoring output.
-- Expected columns: customer_id, churn_probability, scored_at_utc.
DROP VIEW IF EXISTS mart_revenue_at_risk;
CREATE VIEW mart_revenue_at_risk AS
SELECT
    f.customer_id,
    s.churn_probability,
    f.monthly_charges,
    s.churn_probability * f.monthly_charges AS revenue_at_risk,
    c.contract,
    p.payment_method,
    svc.internet_service,
    s.scored_at_utc
FROM scored_customer_churn s
JOIN fact_customer_churn f USING (customer_id)
JOIN dim_contract c USING (contract_id)
JOIN dim_payment p USING (payment_id)
JOIN dim_service svc USING (service_id);
