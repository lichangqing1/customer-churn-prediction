"""Export analytics marts as flat CSV files for Power BI ingestion."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MARTS = (
    "mart_churn_overview",
    "mart_segment_churn",
    "mart_revenue_at_risk",
    "mart_retention_actions",
    "mart_data_quality_status",
)


def export_powerbi_data(
    db_path: str | Path,
    output_dir: str | Path,
    marts: tuple[str, ...] = DEFAULT_MARTS,
) -> dict[str, int]:
    """Export governed mart views and return their row counts."""
    db_path, output_dir = Path(db_path), Path(output_dir)
    if not db_path.is_file():
        raise FileNotFoundError(f"Warehouse not found: {db_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    with sqlite3.connect(db_path) as conn:
        available = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        )}
        missing = sorted(set(marts) - available)
        if missing:
            raise RuntimeError(f"Required marts are missing: {missing}. Run the warehouse build first.")
        for mart in marts:
            frame = pd.read_sql_query(f"SELECT * FROM {mart}", conn)
            frame.to_csv(output_dir / f"{mart}.csv", index=False)
            counts[mart] = len(frame)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=PROJECT_ROOT / "data/warehouse/customer_churn_warehouse.sqlite")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "results/powerbi_exports")
    args = parser.parse_args()
    counts = export_powerbi_data(args.db, args.output_dir)
    print(f"Power BI extracts created in {args.output_dir}")
    for name, rows in counts.items():
        print(f"- {name}: {rows} rows")


if __name__ == "__main__":
    main()
