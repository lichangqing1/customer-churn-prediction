"""Customer-level churn scoring utilities."""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd


def assign_risk_level(
    probability: float,
    threshold_high: float = 0.70,
    threshold_medium: float = 0.40,
) -> str:
    """Convert a churn probability into an operational risk band."""
    if not 0 <= threshold_medium < threshold_high <= 1:
        raise ValueError("Thresholds must satisfy 0 <= medium < high <= 1.")
    if pd.isna(probability) or not 0 <= probability <= 1:
        raise ValueError("Churn probability must be between 0 and 1.")
    if probability >= threshold_high:
        return "High Risk"
    if probability >= threshold_medium:
        return "Medium Risk"
    return "Low Risk"


def score_customers(
    model: Any,
    features: pd.DataFrame,
    customer_ids: Iterable | None = None,
    actual_churn: Iterable | None = None,
    threshold_high: float = 0.70,
    threshold_medium: float = 0.40,
) -> pd.DataFrame:
    """Score customers with a probabilistic classifier and return an action-ready table."""
    if not hasattr(model, "predict_proba"):
        raise TypeError("The scoring model must implement predict_proba().")
    probabilities = np.asarray(model.predict_proba(features))
    if probabilities.ndim != 2 or probabilities.shape[1] < 2:
        raise ValueError("predict_proba() must return probabilities for at least two classes.")

    result = features.copy().reset_index(drop=True)
    if customer_ids is not None:
        ids = pd.Series(customer_ids).reset_index(drop=True)
        if len(ids) != len(result):
            raise ValueError("customer_ids length must match features.")
        result["customer_id"] = ids
    if actual_churn is not None:
        actual = pd.Series(actual_churn).reset_index(drop=True)
        if len(actual) != len(result):
            raise ValueError("actual_churn length must match features.")
        result["actual_churn"] = actual

    result["churn_risk_score"] = probabilities[:, 1]
    result["risk_level"] = result["churn_risk_score"].map(
        lambda value: assign_risk_level(value, threshold_high, threshold_medium)
    )
    if "monthly_charges" in result:
        result["revenue_at_risk"] = result["churn_risk_score"] * pd.to_numeric(
            result["monthly_charges"], errors="raise"
        )
    return result


def create_risk_table(
    features: pd.DataFrame,
    customer_ids: Iterable | None,
    actual_churn: Iterable,
    churn_probabilities: Iterable,
    threshold_high: float = 0.70,
    threshold_medium: float = 0.40,
) -> pd.DataFrame:
    """Create a risk table from probabilities that have already been computed."""
    probabilities = np.asarray(churn_probabilities, dtype=float)
    if len(probabilities) != len(features):
        raise ValueError("churn_probabilities length must match features.")
    result = features.copy().reset_index(drop=True)
    if customer_ids is not None:
        result["customer_id"] = pd.Series(customer_ids).reset_index(drop=True)
    result["actual_churn"] = pd.Series(actual_churn).reset_index(drop=True)
    result["churn_risk_score"] = probabilities
    result["risk_level"] = result["churn_risk_score"].map(
        lambda value: assign_risk_level(value, threshold_high, threshold_medium)
    )
    return result
