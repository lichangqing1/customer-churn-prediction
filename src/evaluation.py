# -*- coding: utf-8 -*-

import pandas as pd
from src.scoring import create_risk_table as _create_risk_table

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)


def evaluate_model(model, X_test, y_test, model_name: str):
    """
    Evaluate a classification model and return metrics.
    """
    y_pred = model.predict(X_test)

    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
        roc_auc = roc_auc_score(y_test, y_proba)
    else:
        y_proba = None
        roc_auc = None

    metrics = {
        "model": model_name,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc
    }

    print(f"Model: {model_name}")
    print(classification_report(y_test, y_pred))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    return metrics, y_pred, y_proba


def compare_models(results: list) -> pd.DataFrame:
    """
    Convert a list of model metric dictionaries into a comparison DataFrame.
    """
    return pd.DataFrame(results).sort_values("recall", ascending=False)


def evaluate_thresholds(y_test, y_proba, thresholds=None) -> pd.DataFrame:
    """
    Evaluate precision, recall, and F1-score at different probability thresholds.
    """
    if thresholds is None:
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]

    threshold_results = []

    for threshold in thresholds:
        y_pred_threshold = (y_proba >= threshold).astype(int)

        threshold_results.append({
            "threshold": threshold,
            "precision": precision_score(y_test, y_pred_threshold),
            "recall": recall_score(y_test, y_pred_threshold),
            "f1_score": f1_score(y_test, y_pred_threshold)
        })

    return pd.DataFrame(threshold_results)


def create_risk_table(
    X_test,
    customer_ids,
    y_test,
    y_proba,
    threshold_high: float = 0.70,
    threshold_medium: float = 0.40
) -> pd.DataFrame:
    """
    Backward-compatible wrapper for the scoring module's risk-table builder.
    """
    return _create_risk_table(
        X_test, customer_ids, y_test, y_proba, threshold_high, threshold_medium
    )
