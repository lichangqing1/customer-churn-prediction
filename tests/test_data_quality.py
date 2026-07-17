import pandas as pd

from src.data_cleaning import prepare_clean_data
from src.data_quality import run_clean_data_quality_checks, assert_quality_checks_passed


def test_clean_data_quality_checks_pass_on_sample():
    raw = pd.DataFrame({
        "customerID": ["A", "B"],
        "gender": ["Female", "Male"],
        "SeniorCitizen": [0, 1],
        "Partner": ["Yes", "No"],
        "Dependents": ["No", "No"],
        "tenure": [1, 10],
        "PhoneService": ["Yes", "Yes"],
        "MultipleLines": ["No", "Yes"],
        "InternetService": ["DSL", "Fiber optic"],
        "OnlineSecurity": ["No", "Yes"],
        "OnlineBackup": ["No", "Yes"],
        "DeviceProtection": ["No", "No"],
        "TechSupport": ["No", "Yes"],
        "StreamingTV": ["No", "Yes"],
        "StreamingMovies": ["No", "No"],
        "Contract": ["Month-to-month", "One year"],
        "PaperlessBilling": ["Yes", "No"],
        "PaymentMethod": ["Electronic check", "Mailed check"],
        "MonthlyCharges": [29.85, 56.95],
        "TotalCharges": ["29.85", "569.5"],
        "Churn": ["No", "Yes"],
    })
    clean = prepare_clean_data(raw)
    results = run_clean_data_quality_checks(clean)
    assert results["passed"].all()
    assert_quality_checks_passed(results)


def test_quality_gate_rejects_duplicate_customer_id():
    raw = pd.DataFrame({
        "customerID": ["A", "A"], "gender": ["Female", "Female"], "SeniorCitizen": [0, 0],
        "Partner": ["No", "No"], "Dependents": ["No", "No"], "tenure": [1, 2],
        "PhoneService": ["Yes", "Yes"], "MultipleLines": ["No", "No"], "InternetService": ["DSL", "DSL"],
        "OnlineSecurity": ["No", "No"], "OnlineBackup": ["No", "No"], "DeviceProtection": ["No", "No"],
        "TechSupport": ["No", "No"], "StreamingTV": ["No", "No"], "StreamingMovies": ["No", "No"],
        "Contract": ["Month-to-month", "Month-to-month"], "PaperlessBilling": ["Yes", "Yes"],
        "PaymentMethod": ["Electronic check", "Electronic check"], "MonthlyCharges": [29.85, 29.85],
        "TotalCharges": ["29.85", "59.70"], "Churn": ["No", "No"],
    })
    clean = prepare_clean_data(raw)
    results = run_clean_data_quality_checks(clean)
    assert not results.loc[results["check_name"] == "require_unique_key", "passed"].item()
