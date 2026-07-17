"""Build the churn warehouse and marts in PostgreSQL."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_quality import run_clean_data_quality_checks, assert_quality_checks_passed
from src.warehouse_builder import (
    load_raw_data, prepare_silver_customers, build_dimension_tables,
    build_fact_table, build_gold_tables,
)


def load_postgres(database_url: str, raw_csv: Path, risk_csv: Path) -> None:
    raw = load_raw_data(raw_csv)
    silver = prepare_silver_customers(raw)
    dimensions = build_dimension_tables(silver)
    fact = build_fact_table(silver, dimensions)
    gold = build_gold_tables(fact, dimensions)
    quality = run_clean_data_quality_checks(silver)
    assert_quality_checks_passed(quality)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    checked_at = datetime.now(timezone.utc).isoformat()
    quality = quality.assign(run_id=run_id, gate="silver", checked_at_utc=checked_at)

    scores = pd.read_csv(risk_csv)[["customer_id", "churn_risk_score"]].rename(
        columns={"churn_risk_score": "churn_probability"}
    )
    scores["churn_probability"] = pd.to_numeric(scores["churn_probability"], errors="raise")
    if scores["customer_id"].duplicated().any() or not scores["churn_probability"].between(0, 1).all():
        raise ValueError("Scoring data failed uniqueness or probability-range validation.")
    scores["scored_at_utc"] = checked_at

    engine = create_engine(database_url)
    with engine.begin() as conn:
        raw.to_sql("bronze_raw_customer_churn", conn, if_exists="replace", index=False)
        silver.to_sql("silver_clean_customers", conn, if_exists="replace", index=False)
        for name, frame in dimensions.items():
            frame.to_sql(name, conn, if_exists="replace", index=False)
        fact.to_sql("fact_customer_churn", conn, if_exists="replace", index=False)
        for name, frame in gold.items():
            frame.to_sql(name, conn, if_exists="replace", index=False)
        scores.to_sql("scored_customer_churn", conn, if_exists="replace", index=False)
        quality.to_sql("meta_data_quality_results", conn, if_exists="replace", index=False)
        pd.DataFrame([{
            "run_id": run_id, "status": "success", "source_rows": len(raw),
            "fact_rows": len(fact), "completed_at_utc": checked_at,
        }]).to_sql("meta_pipeline_runs", conn, if_exists="replace", index=False)
        for statement in (ROOT / "sql/postgres_marts.sql").read_text(encoding="utf-8").split(";"):
            if statement.strip():
                conn.execute(text(statement))
    engine.dispose()
    print(f"PostgreSQL warehouse published: raw={len(raw)}, fact={len(fact)}, scored={len(scores)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--raw-csv", type=Path, default=ROOT / "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")
    parser.add_argument("--risk-csv", type=Path, default=ROOT / "results/risk_table_with_recommendations.csv")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or DATABASE_URL is required")
    load_postgres(args.database_url, args.raw_csv, args.risk_csv)


if __name__ == "__main__":
    main()
