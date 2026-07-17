"""Airflow DAG for the churn warehouse. Airflow is an optional runtime dependency."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CHURN_PROJECT_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from airflow.decorators import dag, task
except ImportError:  # Lets unit tests and linters inspect this module without Airflow.
    dag = task = None


if dag is not None:
    @dag(
        dag_id="customer_churn_warehouse",
        start_date=datetime(2024, 1, 1),
        schedule="0 2 * * *",
        catchup=False,
        max_active_runs=1,
        default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
        tags=["churn", "warehouse", "data-quality"],
    )
    def customer_churn_warehouse():
        @task
        def validate_source() -> str:
            import pandas as pd
            from src.warehouse_builder import prepare_silver_customers
            source = Path(os.environ.get("CHURN_RAW_CSV", PROJECT_ROOT / "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv"))
            if not source.is_file() or source.stat().st_size == 0:
                raise FileNotFoundError(f"Source CSV is missing or empty: {source}")
            prepare_silver_customers(pd.read_csv(source))  # quality gate 1
            return str(source)

        @task
        def build_warehouse(source: str) -> str:
            from src.warehouse_builder import build_churn_warehouse
            target = Path(os.environ.get("CHURN_WAREHOUSE_DB", PROJECT_ROOT / "data/warehouse/customer_churn_warehouse.sqlite"))
            build_churn_warehouse(source, target)  # atomic publish + quality gate 2
            return str(target)

        @task
        def apply_marts(target: str) -> str:
            from scripts.apply_sql_marts import apply_sql_marts
            apply_sql_marts(
                db_path=target,
                marts_dir=PROJECT_ROOT / "sql/marts",
                risk_csv=Path(os.environ.get(
                    "CHURN_RISK_CSV",
                    PROJECT_ROOT / "results/risk_table_with_recommendations.csv",
                )),
                export_dir=PROJECT_ROOT / "results/mart_exports",
            )
            return target

        @task
        def verify_warehouse(target: str) -> None:
            from src.data_quality import run_warehouse_quality_checks, assert_quality_checks_passed
            assert_quality_checks_passed(run_warehouse_quality_checks(target))

        verify_warehouse(apply_marts(build_warehouse(validate_source())))

    churn_warehouse_dag = customer_churn_warehouse()
