-- Requires scored_customer_churn; thresholds match the operational dashboard defaults.
DROP VIEW IF EXISTS mart_retention_actions;
CREATE VIEW mart_retention_actions AS
SELECT
    r.*,
    ROUND(100.0 * revenue_at_risk / MAX(monthly_charges) OVER (), 2) AS retention_priority_score,
    CASE
        WHEN 100.0 * revenue_at_risk / MAX(monthly_charges) OVER () >= 60 THEN 'P1'
        WHEN 100.0 * revenue_at_risk / MAX(monthly_charges) OVER () >= 30 THEN 'P2'
        ELSE 'P3'
    END AS retention_priority,
    revenue_at_risk * 0.20 AS estimated_saved_revenue,
    CASE
        WHEN churn_probability >= 0.70 THEN 'High Risk'
        WHEN churn_probability >= 0.40 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS risk_level,
    CASE
        WHEN churn_probability >= 0.70 AND contract = 'Month-to-month'
            THEN 'Offer long-term contract discount'
        WHEN churn_probability >= 0.70
            THEN 'Priority outreach and personalized retention offer'
        WHEN churn_probability >= 0.40
            THEN 'Proactive service check-in'
        ELSE 'Normal monitoring'
    END AS recommended_action
FROM mart_revenue_at_risk r;
