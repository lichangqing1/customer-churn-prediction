# Customer Churn Business Insights Report

## Executive Summary

The warehouse contains 7,043 customers with an observed churn rate of 26.5%. Churn is concentrated in flexible contracts and manual payment behavior: month-to-month customers churn at 42.7%, while two-year customers churn at only 2.8%. Within the current 1,409-customer scored population, 350 customers exceed the 70% high-risk threshold and probability-weighted monthly revenue at risk is approximately $42,202.51.

## Key Churn Drivers

- Contract commitment is the strongest visible divider. Month-to-month churn is 42.7%, versus 11.3% for one-year and 2.8% for two-year contracts.
- Electronic-check customers churn at 45.3%, compared with 15.2% for automatic credit-card customers.
- Fiber-optic service compounds risk in exposed groups. Month-to-month, electronic-check, fiber-optic customers show a 60.4% churn rate across 1,307 customers.
- Higher charges coincide with several high-risk segments, but these descriptive relationships should not be treated as causal effects.

## Revenue at Risk

Revenue at risk is defined as `churn_probability × monthly_charges`. The current scored population represents about $42.2K of probability-weighted monthly exposure. This expected-value measure prioritizes customers who combine high propensity to churn with meaningful recurring revenue; it is not a prediction that the entire amount will be lost.

## Priority Customer Segments

1. Month-to-month + electronic check + fiber optic: 1,307 customers, 60.4% churn, and average monthly charges of $87.18.
2. Month-to-month + mailed check + fiber optic: 201 customers, 50.7% churn, and average monthly charges of $82.59.
3. Month-to-month + automatic bank transfer + fiber optic: 327 customers, 45.6% churn, and average monthly charges of $88.25.

The first segment deserves the initial campaign because it combines the highest observed rate with the largest exposed population.

### Priority Segment Analysis

| Segment | Churn risk | Revenue impact | Priority | Suggested action |
|---|---|---|---|---|
| Month-to-month + electronic check + fiber optic | Very high (60.4% observed churn) | High: large population with $87.18 average monthly charges | P1 | Contract-upgrade discount combined with automatic-payment enrollment |
| Month-to-month + high monthly charge | High | High | P1 | Retention call, service review, and targeted loyalty offer |
| One-year contract + low tenure | Medium | Medium | P2 | Early-engagement and onboarding campaign before renewal risk increases |

P1 indicates immediate high-touch intervention, P2 indicates proactive campaign
enrollment, and P3 indicates lower-cost monitoring. Operational customer ranking uses
`retention_priority_score`, which combines churn probability and monthly charges on a
0–100 relative scale. `estimated_saved_revenue` applies a 20% planning success rate to
probability-weighted revenue exposure; it should be replaced by measured campaign lift
after controlled experiments.

## Recommended Retention Actions

- Offer a time-bound one-year conversion incentive to high-risk month-to-month customers.
- Pair electronic-check outreach with simple automatic-payment enrollment and a modest bill credit.
- Route high-revenue fiber-optic customers to proactive service reviews before discounting; address experience problems first.
- Use the dashboard’s top-20 revenue-impact list for prioritized human outreach.
- Measure incremental retention through a randomized holdout group, not raw post-campaign churn alone.

## Dashboard Interpretation

The Executive Overview is the daily decision page. Churn Segments explains where risk is concentrated. High-Risk Customers is the operational retention queue. Revenue at Risk ranks expected financial impact. Data Quality confirms whether the displayed warehouse passed its latest pipeline gates. Dashboard threshold changes are exploratory and should be recorded when customer lists are exported.

## Data Quality Notes

The pipeline validates required columns, customer uniqueness, required non-null fields, numeric ranges, fact-to-Silver reconciliation, dimension referential integrity, and Gold churn-rate ranges. Results are persisted in `meta_data_quality_results`, with run status in `meta_pipeline_runs`. A warehouse is published atomically only after all enforced gates pass.

## Limitations

- Model scores cover 1,409 customers rather than the full 7,043-customer warehouse population.
- The source is a static public snapshot without event dates, acquisition cohorts, campaign costs, or service-interaction history.
- Revenue at risk excludes margin, customer lifetime value, intervention cost, and probability calibration uncertainty.
- Segment findings are observational and do not establish that a contract, payment method, or service causes churn.
- The dashboard reflects batch artifacts and is not a real-time operational system.

## Next Steps

1. Score the full active customer population and load a governed `scored_customer_churn` table.
2. Add score timestamp, model version, threshold, and calibration monitoring.
3. Add customer lifetime value and campaign cost to optimize expected net retention value.
4. Track intervention, control-group assignment, acceptance, and retained-revenue outcomes.
5. Schedule mart creation after warehouse publication and expose freshness SLAs in the dashboard.
