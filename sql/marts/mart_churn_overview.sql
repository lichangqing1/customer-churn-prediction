-- One-row executive overview at the customer snapshot grain.
DROP VIEW IF EXISTS mart_churn_overview;
CREATE VIEW mart_churn_overview AS
SELECT
    COUNT(DISTINCT customer_id) AS total_customers,
    AVG(churn_flag * 1.0) AS overall_churn_rate,
    SUM(monthly_charges) AS total_monthly_revenue,
    AVG(monthly_charges) AS avg_monthly_charges
FROM fact_customer_churn;
