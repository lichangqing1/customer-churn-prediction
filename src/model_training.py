# -*- coding: utf-8 -*-


import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


def split_features_target(
    df: pd.DataFrame,
    target_col: str = "churn_flag",
    id_col: str = "customer_id",
    drop_cols: list | None = None
):
    """
    Split dataset into X, y, and customer IDs.
    """
    df = df.copy()

    if drop_cols is None:
        drop_cols = ["customer_id", "churn", target_col]

    customer_ids = df[id_col] if id_col in df.columns else None

    X = df.drop(columns=drop_cols, errors="ignore")
    y = df[target_col]

    return X, y, customer_ids


def get_column_types(X: pd.DataFrame):
    """
    Identify categorical and numeric columns.
    """
    categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    numeric_cols = X.select_dtypes(include=["int64", "float64", "int32", "float32"]).columns.tolist()

    return categorical_cols, numeric_cols


def build_preprocessor(X: pd.DataFrame):
    """
    Build preprocessing pipeline for numeric and categorical features.
    """
    categorical_cols, numeric_cols = get_column_types(X)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)
        ]
    )

    return preprocessor


def create_logistic_regression_model(preprocessor, random_state: int = 42):
    """
    Create Logistic Regression pipeline.
    """
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=random_state
            ))
        ]
    )

    return model


def create_random_forest_model(preprocessor, random_state: int = 42):
    """
    Create Random Forest pipeline.
    """
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=200,
                random_state=random_state,
                class_weight="balanced",
                n_jobs=-1
            ))
        ]
    )

    return model

def train_test_split_with_ids(
    X,
    y,
    customer_ids=None,
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Train-test split with optional customer IDs.
    """
    if customer_ids is not None:
        return train_test_split(
            X,
            y,
            customer_ids,
            test_size=test_size,
            random_state=random_state,
            stratify=y
        )

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )
