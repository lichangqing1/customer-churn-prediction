import sqlite3

import pandas as pd

from scripts.apply_sql_marts import apply_sql_marts
from src.warehouse_builder import build_churn_warehouse
from tests.test_warehouse_builder import _sample_raw


def test_apply_sql_marts_loads_scores_creates_views_and_exports(tmp_path):
    source = tmp_path / "source.csv"
    database = tmp_path / "warehouse.sqlite"
    scores = tmp_path / "scores.csv"
    exports = tmp_path / "exports"
    _sample_raw().to_csv(source, index=False)
    build_churn_warehouse(source, database)
    pd.DataFrame({
        "customer_id": ["A", "B", "C"],
        "churn_risk_score": [0.8, 0.5, 0.1],
    }).to_csv(scores, index=False)

    marts = apply_sql_marts(database, "sql/marts", scores, exports)

    assert set(marts) == {
        "mart_churn_overview", "mart_segment_churn", "mart_revenue_at_risk",
        "mart_retention_actions", "mart_data_quality_status",
    }
    assert marts["mart_revenue_at_risk"]["revenue_at_risk"].notna().all()
    assert (exports / "mart_retention_actions.csv").is_file()
    with sqlite3.connect(database) as conn:
        views = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        )}
    assert set(marts).issubset(views)
