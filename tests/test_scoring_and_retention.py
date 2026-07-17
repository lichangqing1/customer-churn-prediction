import numpy as np
import pandas as pd

from src.retention_recommendations import add_retention_recommendations
from src.scoring import assign_risk_level, score_customers


class _Model:
    def predict_proba(self, features):
        positive = np.array([0.8, 0.5, 0.1])
        return np.column_stack([1 - positive, positive])


def test_score_customers_adds_risk_and_revenue_at_risk():
    features = pd.DataFrame({"monthly_charges": [100.0, 60.0, 20.0]})
    scored = score_customers(_Model(), features, ["A", "B", "C"], [1, 0, 0])
    assert scored["risk_level"].tolist() == ["High Risk", "Medium Risk", "Low Risk"]
    assert scored["revenue_at_risk"].tolist() == [80.0, 30.0, 2.0]


def test_retention_rules_prioritize_contract_conversion():
    scored = pd.DataFrame({
        "risk_level": ["High Risk", "High Risk", "Medium Risk", "Low Risk"],
        "contract": ["Month-to-month", "One year", "One year", "Two year"],
        "monthly_charges": [90, 80, 60, 50],
    })
    result = add_retention_recommendations(scored)
    assert result["recommended_action"].tolist() == [
        "Offer long-term contract discount", "Offer personalized price discount",
        "Send satisfaction survey and retention message", "Normal monitoring",
    ]


def test_risk_thresholds_are_validated():
    assert assign_risk_level(0.70) == "High Risk"
    try:
        assign_risk_level(0.5, threshold_high=0.4, threshold_medium=0.7)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid thresholds must fail")
