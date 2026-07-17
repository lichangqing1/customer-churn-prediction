"""Build a lightweight SQLite analytics warehouse for churn analysis.

The goal is to demonstrate data-engineering skills: layered data modeling,
quality checks, analytics tables, and reproducible pipeline outputs.
"""
from __future__ import annotations

import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data_cleaning import prepare_clean_data, validate_clean_data
from src.feature_engineering import add_churn_features, create_tenure_group, create_monthly_charge_group
from src.data_quality import (
    run_clean_data_quality_checks, assert_quality_checks_passed,
    run_warehouse_quality_checks,
)


def load_raw_data(raw_csv_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(raw_csv_path)


def prepare_silver_customers(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and feature-engineer the raw churn data."""
    clean_df = prepare_clean_data(raw_df)
    validate_clean_data(clean_df)
    quality_results = run_clean_data_quality_checks(clean_df)
    assert_quality_checks_passed(quality_results)
    clean_df = add_churn_features(clean_df)
    clean_df = create_tenure_group(clean_df)
    clean_df = create_monthly_charge_group(clean_df)
    return clean_df


def build_dimension_tables(silver_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create simple dimension tables for a star-schema style warehouse."""
    dim_customer = silver_df[[
        "customer_id", "gender", "senior_citizen", "partner", "dependents"
    ]].drop_duplicates("customer_id")

    dim_contract = (
        silver_df[["contract"]]
        .drop_duplicates()
        .sort_values("contract")
        .reset_index(drop=True)
        .reset_index()
        .rename(columns={"index": "contract_id"})
    )
    dim_contract["contract_id"] = dim_contract["contract_id"] + 1

    dim_service = (
        silver_df[["internet_service", "phone_service", "online_security", "tech_support"]]
        .drop_duplicates()
        .reset_index(drop=True)
        .reset_index()
        .rename(columns={"index": "service_id"})
    )
    dim_service["service_id"] = dim_service["service_id"] + 1

    dim_payment = (
        silver_df[["payment_method", "paperless_billing"]]
        .drop_duplicates()
        .reset_index(drop=True)
        .reset_index()
        .rename(columns={"index": "payment_id"})
    )
    dim_payment["payment_id"] = dim_payment["payment_id"] + 1

    return {
        "dim_customer": dim_customer,
        "dim_contract": dim_contract,
        "dim_service": dim_service,
        "dim_payment": dim_payment,
    }


def build_fact_table(silver_df: pd.DataFrame, dimensions: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create a customer-level churn fact table."""
    fact = silver_df[[
        "customer_id", "contract", "internet_service", "phone_service", "online_security",
        "tech_support", "payment_method", "paperless_billing", "tenure",
        "monthly_charges", "total_charges", "avg_charge_per_tenure", "high_monthly_charge",
        "short_tenure", "is_long_term_contract", "tenure_group", "monthly_charge_group",
        "churn_flag",
    ]].copy()

    fact = fact.merge(dimensions["dim_contract"], on="contract", how="left")
    fact = fact.merge(
        dimensions["dim_service"],
        on=["internet_service", "phone_service", "online_security", "tech_support"],
        how="left",
    )
    fact = fact.merge(dimensions["dim_payment"], on=["payment_method", "paperless_billing"], how="left")
    fact = fact.drop(columns=[
        "contract", "internet_service", "phone_service", "online_security", "tech_support",
        "payment_method", "paperless_billing",
    ])
    return fact


def build_gold_tables(fact: pd.DataFrame, dimensions: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    fact_with_dims = fact.merge(dimensions["dim_contract"], on="contract_id", how="left")
    fact_with_dims = fact_with_dims.merge(dimensions["dim_payment"], on="payment_id", how="left")
    fact_with_dims = fact_with_dims.merge(dimensions["dim_service"], on="service_id", how="left")

    churn_by_contract = (
        fact_with_dims.groupby("contract", as_index=False)
        .agg(customers=("customer_id", "count"), churn_rate=("churn_flag", "mean"), avg_monthly_charges=("monthly_charges", "mean"))
        .sort_values("churn_rate", ascending=False)
    )

    churn_by_payment = (
        fact_with_dims.groupby("payment_method", as_index=False)
        .agg(customers=("customer_id", "count"), churn_rate=("churn_flag", "mean"), avg_monthly_charges=("monthly_charges", "mean"))
        .sort_values("churn_rate", ascending=False)
    )

    high_risk_segments = (
        fact_with_dims.groupby(["contract", "payment_method", "internet_service"], as_index=False)
        .agg(customers=("customer_id", "count"), churn_rate=("churn_flag", "mean"), avg_monthly_charges=("monthly_charges", "mean"))
        .query("customers >= 20")
        .sort_values("churn_rate", ascending=False)
    )

    return {
        "gold_churn_by_contract": churn_by_contract,
        "gold_churn_by_payment": churn_by_payment,
        "gold_high_risk_segments": high_risk_segments,
    }


def write_sqlite_warehouse(
    raw_df: pd.DataFrame,
    silver_df: pd.DataFrame,
    dimensions: dict[str, pd.DataFrame],
    fact: pd.DataFrame,
    gold_tables: dict[str, pd.DataFrame],
    output_db_path: str | Path,
) -> None:
    output_db_path = Path(output_db_path)
    output_db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_db_path.with_suffix(output_db_path.suffix + ".tmp")
    # Avoid Path.unlink(missing_ok=True) for compatibility with older pathlib
    # implementations that may be present in existing virtual environments.
    if temporary_path.exists():
        temporary_path.unlink()
    with sqlite3.connect(temporary_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        raw_df.to_sql("bronze_raw_customer_churn", conn, if_exists="replace", index=False)
        silver_df.to_sql("silver_clean_customers", conn, if_exists="replace", index=False)
        for table_name, table_df in dimensions.items():
            table_df.to_sql(table_name, conn, if_exists="replace", index=False)
        fact.to_sql("fact_customer_churn", conn, if_exists="replace", index=False)
        for table_name, table_df in gold_tables.items():
            table_df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.execute("CREATE UNIQUE INDEX ux_dim_customer ON dim_customer(customer_id)")
        conn.execute("CREATE UNIQUE INDEX ux_dim_contract ON dim_contract(contract_id)")
        conn.execute("CREATE UNIQUE INDEX ux_dim_service ON dim_service(service_id)")
        conn.execute("CREATE UNIQUE INDEX ux_dim_payment ON dim_payment(payment_id)")
        conn.execute("CREATE UNIQUE INDEX ux_fact_customer ON fact_customer_churn(customer_id)")
    warehouse_results = run_warehouse_quality_checks(temporary_path)
    assert_quality_checks_passed(warehouse_results)
    silver_results = run_clean_data_quality_checks(silver_df)
    assert_quality_checks_passed(silver_results)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    checked_at = datetime.now(timezone.utc).isoformat()
    audit_results = pd.concat([
        silver_results.assign(gate="silver"),
        warehouse_results.assign(gate="warehouse"),
    ], ignore_index=True).assign(run_id=run_id, checked_at_utc=checked_at)
    with sqlite3.connect(temporary_path) as conn:
        audit_results.to_sql("meta_data_quality_results", conn, if_exists="replace", index=False)
        pd.DataFrame([{
            "run_id": run_id, "status": "success", "source_rows": len(raw_df),
            "fact_rows": len(fact), "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        }]).to_sql("meta_pipeline_runs", conn, if_exists="replace", index=False)
    os.replace(temporary_path, output_db_path)


def build_churn_warehouse(raw_csv_path: str | Path, output_db_path: str | Path) -> dict[str, pd.DataFrame]:
    raw_df = load_raw_data(raw_csv_path)
    silver_df = prepare_silver_customers(raw_df)
    dimensions = build_dimension_tables(silver_df)
    fact = build_fact_table(silver_df, dimensions)
    gold_tables = build_gold_tables(fact, dimensions)
    write_sqlite_warehouse(raw_df, silver_df, dimensions, fact, gold_tables, output_db_path)
    return {
        "bronze_raw_customer_churn": raw_df,
        "silver_clean_customers": silver_df,
        **dimensions,
        "fact_customer_churn": fact,
        **gold_tables,
    }
