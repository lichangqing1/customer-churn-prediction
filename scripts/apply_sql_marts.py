"""Apply analytics mart SQL to the warehouse and export mart results."""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MART_FILES = (
    "mart_churn_overview.sql",
    "mart_segment_churn.sql",
    "mart_revenue_at_risk.sql",
    "mart_retention_actions.sql",
    "mart_data_quality_status.sql",
)


def load_scored_customers(conn: sqlite3.Connection, risk_csv: str | Path) -> int:
    """Load the governed subset of model output required by SQL marts."""
    risk_csv = Path(risk_csv)
    if not risk_csv.is_file():
        raise FileNotFoundError(f"Scored customer artifact not found: {risk_csv}")
    scored = pd.read_csv(risk_csv)
    required = {"customer_id", "churn_risk_score"}
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"Scored customer artifact is missing columns: {missing}")
    scored = scored[["customer_id", "churn_risk_score"]].rename(
        columns={"churn_risk_score": "churn_probability"}
    )
    scored["churn_probability"] = pd.to_numeric(scored["churn_probability"], errors="raise")
    if not scored["churn_probability"].between(0, 1).all():
        raise ValueError("churn_probability must be between 0 and 1.")
    if scored["customer_id"].duplicated().any():
        raise ValueError("Scored customer artifact contains duplicate customer_id values.")
    scored["scored_at_utc"] = datetime.now(timezone.utc).isoformat()
    scored.to_sql("scored_customer_churn", conn, if_exists="replace", index=False)
    conn.execute("CREATE UNIQUE INDEX ux_scored_customer ON scored_customer_churn(customer_id)")
    return len(scored)


def apply_sql_marts(
    db_path: str | Path,
    marts_dir: str | Path,
    risk_csv: str | Path,
    export_dir: str | Path,
) -> dict[str, pd.DataFrame]:
    """Load scores, create mart views in dependency order, and export each mart."""
    db_path, marts_dir, export_dir = Path(db_path), Path(marts_dir), Path(export_dir)
    if not db_path.is_file():
        raise FileNotFoundError(f"Warehouse not found: {db_path}")
    scripts = [marts_dir / name for name in MART_FILES]
    missing = [str(path) for path in scripts if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Mart SQL files not found: {missing}")

    with sqlite3.connect(db_path) as conn:
        load_scored_customers(conn, risk_csv)
        for sql_file in scripts:
            conn.executescript(sql_file.read_text(encoding="utf-8"))
        results = {
            Path(name).stem: pd.read_sql_query(f"SELECT * FROM {Path(name).stem}", conn)
            for name in MART_FILES
        }

    export_dir.mkdir(parents=True, exist_ok=True)
    for mart_name, frame in results.items():
        frame.to_csv(export_dir / f"{mart_name}.csv", index=False)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=PROJECT_ROOT / "data/warehouse/customer_churn_warehouse.sqlite", type=Path)
    parser.add_argument("--marts-dir", default=PROJECT_ROOT / "sql/marts", type=Path)
    parser.add_argument("--risk-csv", default=PROJECT_ROOT / "results/risk_table_with_recommendations.csv", type=Path)
    parser.add_argument("--export-dir", default=PROJECT_ROOT / "results/mart_exports", type=Path)
    args = parser.parse_args()
    marts = apply_sql_marts(args.db, args.marts_dir, args.risk_csv, args.export_dir)
    print(f"Applied and exported {len(marts)} marts to {args.db}")
    for name, frame in marts.items():
        print(f"- {name}: {len(frame)} rows")


if __name__ == "__main__":
    main()
