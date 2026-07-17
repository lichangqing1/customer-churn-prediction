import pandas as pd
import sqlite3

from src.warehouse_builder import prepare_silver_customers, build_dimension_tables, build_fact_table, build_gold_tables, build_churn_warehouse
from src.data_quality import run_warehouse_quality_checks


def _sample_raw():
    return pd.DataFrame({
        "customerID": ["A", "B", "C"],
        "gender": ["Female", "Male", "Female"],
        "SeniorCitizen": [0, 1, 0],
        "Partner": ["Yes", "No", "No"],
        "Dependents": ["No", "No", "Yes"],
        "tenure": [1, 10, 30],
        "PhoneService": ["Yes", "Yes", "No"],
        "MultipleLines": ["No", "Yes", "No phone service"],
        "InternetService": ["DSL", "Fiber optic", "DSL"],
        "OnlineSecurity": ["No", "Yes", "Yes"],
        "OnlineBackup": ["No", "Yes", "No"],
        "DeviceProtection": ["No", "No", "Yes"],
        "TechSupport": ["No", "Yes", "Yes"],
        "StreamingTV": ["No", "Yes", "No"],
        "StreamingMovies": ["No", "No", "No"],
        "Contract": ["Month-to-month", "One year", "Two year"],
        "PaperlessBilling": ["Yes", "No", "No"],
        "PaymentMethod": ["Electronic check", "Mailed check", "Bank transfer (automatic)"],
        "MonthlyCharges": [29.85, 56.95, 42.30],
        "TotalCharges": ["29.85", "569.5", "1269.0"],
        "Churn": ["No", "Yes", "No"],
    })


def test_build_star_schema_tables():
    silver = prepare_silver_customers(_sample_raw())
    dimensions = build_dimension_tables(silver)
    fact = build_fact_table(silver, dimensions)
    gold = build_gold_tables(fact, dimensions)

    assert len(dimensions["dim_customer"]) == 3
    assert "contract_id" in fact.columns
    assert "service_id" in fact.columns
    assert "payment_id" in fact.columns
    assert "gold_churn_by_contract" in gold


def test_end_to_end_warehouse_has_passing_audit(tmp_path):
    source = tmp_path / "source.csv"
    target = tmp_path / "warehouse.sqlite"
    _sample_raw().to_csv(source, index=False)
    build_churn_warehouse(source, target)

    assert run_warehouse_quality_checks(target)["passed"].all()
    with sqlite3.connect(target) as conn:
        audit = pd.read_sql_query("SELECT * FROM meta_data_quality_results", conn)
        runs = pd.read_sql_query("SELECT * FROM meta_pipeline_runs", conn)
    assert audit["passed"].all()
    assert runs.loc[0, "status"] == "success"
