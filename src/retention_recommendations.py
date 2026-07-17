"""Rules that translate customer risk into retention actions."""
from __future__ import annotations

import pandas as pd


def recommend_retention_action(row: pd.Series) -> str:
    """Return the standard intervention for one scored customer."""
    risk_level = row.get("risk_level")
    if risk_level == "High Risk":
        if row.get("contract") == "Month-to-month":
            return "Offer long-term contract discount"
        if pd.notna(row.get("monthly_charges")) and float(row["monthly_charges"]) > 70:
            return "Offer personalized price discount"
        return "Priority customer service follow-up"
    if risk_level == "Medium Risk":
        return "Send satisfaction survey and retention message"
    if risk_level == "Low Risk":
        return "Normal monitoring"
    raise ValueError(f"Unsupported risk level: {risk_level!r}")


def add_retention_recommendations(risk_table: pd.DataFrame) -> pd.DataFrame:
    """Add a recommended_action column without mutating the input table."""
    if "risk_level" not in risk_table:
        raise KeyError("risk_table must contain a risk_level column.")
    result = risk_table.copy()
    result["recommended_action"] = result.apply(recommend_retention_action, axis=1)
    return result
