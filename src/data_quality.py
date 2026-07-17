"""Data quality checks for the customer churn project.

These functions are designed for both analytics and data-engineering style
interviews. They validate raw/cleaned datasets before model training or loading
into the SQLite warehouse.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import sqlite3
from pathlib import Path

import pandas as pd


@dataclass
class QualityCheckResult:
    check_name: str
    passed: bool
    details: str


def require_columns(df: pd.DataFrame, columns: Iterable[str]) -> QualityCheckResult:
    missing = [col for col in columns if col not in df.columns]
    return QualityCheckResult(
        check_name="require_columns",
        passed=not missing,
        details="All required columns exist." if not missing else f"Missing columns: {missing}",
    )


def require_unique_key(df: pd.DataFrame, key: str) -> QualityCheckResult:
    if key not in df.columns:
        return QualityCheckResult("require_unique_key", False, f"Key column not found: {key}")
    duplicated = int(df[key].duplicated().sum())
    return QualityCheckResult(
        check_name="require_unique_key",
        passed=duplicated == 0,
        details=f"Duplicated {key} values: {duplicated}",
    )


def require_non_null(df: pd.DataFrame, columns: Iterable[str]) -> QualityCheckResult:
    missing_counts = {col: int(df[col].isna().sum()) for col in columns if col in df.columns}
    failed = {col: count for col, count in missing_counts.items() if count > 0}
    return QualityCheckResult(
        check_name="require_non_null",
        passed=not failed,
        details="No nulls in required columns." if not failed else f"Null counts: {failed}",
    )


def require_values_in_set(df: pd.DataFrame, column: str, allowed_values: set) -> QualityCheckResult:
    if column not in df.columns:
        return QualityCheckResult("require_values_in_set", False, f"Column not found: {column}")
    invalid = sorted(set(df[column].dropna().unique()) - set(allowed_values))
    return QualityCheckResult(
        check_name="require_values_in_set",
        passed=not invalid,
        details="All values are valid." if not invalid else f"Invalid values in {column}: {invalid}",
    )


def require_numeric_range(df: pd.DataFrame, column: str, minimum: float | None = None, maximum: float | None = None) -> QualityCheckResult:
    if column not in df.columns:
        return QualityCheckResult("require_numeric_range", False, f"Column not found: {column}")
    series = pd.to_numeric(df[column], errors="coerce")
    invalid_null = int(series.isna().sum())
    invalid_low = int((series < minimum).sum()) if minimum is not None else 0
    invalid_high = int((series > maximum).sum()) if maximum is not None else 0
    passed = invalid_null == 0 and invalid_low == 0 and invalid_high == 0
    details = f"null_or_non_numeric={invalid_null}, below_min={invalid_low}, above_max={invalid_high}"
    return QualityCheckResult("require_numeric_range", passed, details)


def run_clean_data_quality_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Run the default quality checks for the cleaned churn dataset."""
    checks = [
        require_columns(
            df,
            [
                "customer_id", "tenure", "monthly_charges", "total_charges",
                "contract", "payment_method", "churn", "churn_flag",
            ],
        ),
        require_unique_key(df, "customer_id"),
        require_non_null(df, ["customer_id", "tenure", "monthly_charges", "total_charges", "churn_flag"]),
        require_values_in_set(df, "churn_flag", {0, 1}),
        require_numeric_range(df, "tenure", minimum=0, maximum=100),
        require_numeric_range(df, "monthly_charges", minimum=0),
        require_numeric_range(df, "total_charges", minimum=0),
    ]
    return pd.DataFrame([check.__dict__ for check in checks])


def assert_quality_checks_passed(results: pd.DataFrame) -> None:
    """Raise an AssertionError if any quality checks failed."""
    failed = results[~results["passed"]]
    if not failed.empty:
        details = "; ".join(f"{row.check_name}: {row.details}" for row in failed.itertuples())
        raise AssertionError(f"Data quality checks failed: {details}")


def run_warehouse_quality_checks(db_path: str | Path) -> pd.DataFrame:
    """Validate the published warehouse, including fact/dimension integrity."""
    checks: list[QualityCheckResult] = []
    required_tables = {
        "bronze_raw_customer_churn", "silver_clean_customers", "dim_customer",
        "dim_contract", "dim_service", "dim_payment", "fact_customer_churn",
        "gold_churn_by_contract", "gold_churn_by_payment", "gold_high_risk_segments",
    }
    with sqlite3.connect(db_path) as conn:
        actual = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}
        missing = sorted(required_tables - actual)
        checks.append(QualityCheckResult(
            "warehouse_required_tables", not missing,
            "All required tables exist." if not missing else f"Missing tables: {missing}",
        ))
        if missing:
            return pd.DataFrame([check.__dict__ for check in checks])

        fact_rows = conn.execute("SELECT COUNT(*) FROM fact_customer_churn").fetchone()[0]
        silver_rows = conn.execute("SELECT COUNT(*) FROM silver_clean_customers").fetchone()[0]
        checks.append(QualityCheckResult(
            "fact_silver_row_count", fact_rows == silver_rows,
            f"fact_rows={fact_rows}, silver_rows={silver_rows}",
        ))
        duplicate_facts = conn.execute(
            "SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM fact_customer_churn"
        ).fetchone()[0]
        checks.append(QualityCheckResult(
            "fact_customer_unique", duplicate_facts == 0,
            f"duplicate_customer_ids={duplicate_facts}",
        ))
        orphan_query = """
            SELECT COUNT(*) FROM fact_customer_churn f
            LEFT JOIN dim_customer c ON f.customer_id = c.customer_id
            LEFT JOIN dim_contract ct ON f.contract_id = ct.contract_id
            LEFT JOIN dim_service s ON f.service_id = s.service_id
            LEFT JOIN dim_payment p ON f.payment_id = p.payment_id
            WHERE c.customer_id IS NULL OR ct.contract_id IS NULL
               OR s.service_id IS NULL OR p.payment_id IS NULL
        """
        orphans = conn.execute(orphan_query).fetchone()[0]
        checks.append(QualityCheckResult(
            "fact_dimension_referential_integrity", orphans == 0,
            f"orphan_fact_rows={orphans}",
        ))
        invalid_rates = 0
        for table in ("gold_churn_by_contract", "gold_churn_by_payment", "gold_high_risk_segments"):
            invalid_rates += conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE churn_rate < 0 OR churn_rate > 1 OR churn_rate IS NULL"
            ).fetchone()[0]
        checks.append(QualityCheckResult(
            "gold_churn_rate_range", invalid_rates == 0,
            f"invalid_gold_rows={invalid_rates}",
        ))
    return pd.DataFrame([check.__dict__ for check in checks])
