"""Build the churn analytics SQLite warehouse."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.warehouse_builder import build_churn_warehouse
from scripts.apply_sql_marts import apply_sql_marts


def main() -> None:
    raw_csv = PROJECT_ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
    output_db = PROJECT_ROOT / "data" / "warehouse" / "customer_churn_warehouse.sqlite"
    tables = build_churn_warehouse(raw_csv, output_db)

    output_dir = PROJECT_ROOT / "results" / "warehouse_exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, table_df in tables.items():
        if table_name.startswith("gold_"):
            table_df.to_csv(output_dir / f"{table_name}.csv", index=False)

    marts = apply_sql_marts(
        db_path=output_db,
        marts_dir=PROJECT_ROOT / "sql" / "marts",
        risk_csv=PROJECT_ROOT / "results" / "risk_table_with_recommendations.csv",
        export_dir=PROJECT_ROOT / "results" / "mart_exports",
    )

    print(f"Warehouse created: {output_db}")
    for table_name, table_df in tables.items():
        print(f"- {table_name}: {len(table_df)} rows")
    print("SQL marts applied and exported:")
    for mart_name, mart_df in marts.items():
        print(f"- {mart_name}: {len(mart_df)} rows")


if __name__ == "__main__":
    main()
