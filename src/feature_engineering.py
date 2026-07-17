# -*- coding: utf-8 -*-

import pandas as pd


def add_churn_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add business-oriented features for churn prediction.
    """
    df = df.copy()

    required_columns = ["total_charges", "tenure", "monthly_charges", "contract"]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for feature engineering: {missing_columns}")

    df["avg_charge_per_tenure"] = df["total_charges"] / (df["tenure"] + 1)

    df["high_monthly_charge"] = (
        df["monthly_charges"] > df["monthly_charges"].median()
    ).astype(int)

    df["short_tenure"] = (df["tenure"] <= 12).astype(int)

    df["is_long_term_contract"] = df["contract"].isin(
        ["One year", "Two year"]
    ).astype(int)

    return df


def create_tenure_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create tenure group for business analysis.
    """
    df = df.copy()

    df["tenure_group"] = pd.cut(
        df["tenure"],
        bins=[0, 12, 24, 48, 72],
        labels=["0-12 months", "13-24 months", "25-48 months", "49-72 months"],
        include_lowest=True
    )

    return df


def create_monthly_charge_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create monthly charge group for business analysis.
    """
    df = df.copy()

    df["monthly_charge_group"] = pd.cut(
        df["monthly_charges"],
        bins=[0, 35, 70, 120],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )

    return df

