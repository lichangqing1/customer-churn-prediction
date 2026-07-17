"""Streamlit decision-support dashboard for the churn analytics warehouse."""
from __future__ import annotations

import sqlite3
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data/warehouse/customer_churn_warehouse.sqlite"
DEFAULT_SOURCE = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")

st.set_page_config(page_title="Customer Churn Command Center", page_icon="📉", layout="wide")


@st.cache_data(show_spinner=False)
def load_dashboard_data(database_url: str) -> dict[str, pd.DataFrame]:
    """Load business and observability datasets from stable local artifacts."""
    if database_url.startswith("sqlite:///"):
        db = Path(database_url.removeprefix("sqlite:///"))
        if not db.is_file():
            raise FileNotFoundError(f"Warehouse not found: {db}")
    engine = create_engine(database_url)
    inspector = inspect(engine)
    tables, views = set(inspector.get_table_names()), set(inspector.get_view_names())
    with engine.connect() as conn:
        required_marts = {
            "mart_churn_overview", "mart_segment_churn", "mart_revenue_at_risk",
            "mart_retention_actions", "mart_data_quality_status",
        }
        missing_marts = sorted(required_marts - views)
        if missing_marts:
            raise RuntimeError(f"Warehouse marts are missing: {missing_marts}. Rebuild the warehouse.")
        def query(sql: str) -> pd.DataFrame:
            return pd.read_sql_query(text(sql), conn)

        segment_mart = query("SELECT * FROM mart_segment_churn")
        data = {
            "overview": query("SELECT * FROM mart_churn_overview"),
            "contract": segment_mart.query("segment_type == 'contract'").rename(columns={"segment_value": "contract"}),
            "payment": segment_mart.query("segment_type == 'payment_method'").rename(columns={"segment_value": "payment_method"}),
            "internet": segment_mart.query("segment_type == 'internet_service'").rename(columns={"segment_value": "internet_service"}),
            "segments": segment_mart.query("segment_type == 'combined_risk_segment'").sort_values("churn_rate", ascending=False),
            "risk": query("SELECT * FROM mart_retention_actions"),
            "quality_status": query("SELECT * FROM mart_data_quality_status"),
        }
        counts = {}
        for name in ("bronze_raw_customer_churn", "silver_clean_customers", "fact_customer_churn"):
            counts[name] = conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
        data["counts"] = pd.DataFrame([counts])
        if "meta_pipeline_runs" in tables:
            data["runs"] = query("SELECT * FROM meta_pipeline_runs ORDER BY completed_at_utc DESC LIMIT 1")
        else:
            data["runs"] = pd.DataFrame()
        if "meta_data_quality_results" in tables:
            data["quality"] = query("""
                SELECT * FROM meta_data_quality_results
                WHERE run_id = (SELECT run_id FROM meta_pipeline_runs ORDER BY completed_at_utc DESC LIMIT 1)
            """, conn)
        else:
            data["quality"] = pd.DataFrame()

    return data


def money(value: float) -> str:
    return f"${value:,.2f}"


st.title("Customer Churn Command Center")
st.caption("Warehouse KPIs, retention priorities, revenue exposure, and pipeline health")

with st.sidebar:
    st.header("Data sources")
    database_url = st.text_input("Warehouse URL", DEFAULT_SOURCE, help="SQLite or PostgreSQL SQLAlchemy URL")
    high_risk_threshold = st.slider("High-risk probability", 0.50, 0.95, 0.70, 0.05)
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()

try:
    data = load_dashboard_data(database_url)
except (FileNotFoundError, RuntimeError, sqlite3.Error, pd.errors.ParserError, Exception) as exc:
    st.error(str(exc))
    st.info("Run `python scripts/build_churn_warehouse.py` and the model scoring workflow, then refresh.")
    st.stop()

risk = data["risk"]
high_risk = risk[risk["churn_probability"] >= high_risk_threshold].copy()
total_customers = int(data["counts"]["fact_customer_churn"].iloc[0])
overall_churn = float(data["overview"]["overall_churn_rate"].iloc[0])

overview, segments_tab, customers_tab, revenue_tab, quality_tab = st.tabs([
    "Executive Overview", "Churn Segments", "High-Risk Customers", "Revenue at Risk", "Data Quality",
])

with overview:
    cols = st.columns(5)
    cols[0].metric("Total customers", f"{total_customers:,}")
    cols[1].metric("Overall churn rate", f"{overall_churn:.1%}")
    cols[2].metric("High-risk customers", f"{len(high_risk):,}", help=f"Probability ≥ {high_risk_threshold:.0%}")
    cols[3].metric("Monthly revenue at risk", money(risk["revenue_at_risk"].sum()))
    cols[4].metric("Estimated saved revenue", money(risk["estimated_saved_revenue"].sum()), help="Scenario using a 20% intervention success assumption")

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Top 3 churn-risk segments")
        top = data["segments"].head(3).copy()
        top["churn_rate"] = top["churn_rate"].map(lambda x: f"{x:.1%}")
        top["avg_monthly_charges"] = top["avg_monthly_charges"].map(money)
        st.dataframe(top, hide_index=True, use_container_width=True)
    with right:
        st.subheader("Recommended action summary")
        actions = high_risk["recommended_action"].value_counts().rename_axis("action").reset_index(name="customers")
        st.dataframe(actions, hide_index=True, use_container_width=True)

    st.subheader("Priority Segment Analysis")
    priority_segments = risk.groupby(
        ["contract", "payment_method", "internet_service"], as_index=False
    ).agg(
        high_risk_customer_count=("churn_probability", lambda values: int((values >= high_risk_threshold).sum())),
        avg_churn_probability=("churn_probability", "mean"),
        revenue_at_risk=("revenue_at_risk", "sum"),
        estimated_saved_revenue=("estimated_saved_revenue", "sum"),
    )
    priority_segments = priority_segments[priority_segments["high_risk_customer_count"] > 0]
    max_revenue = priority_segments["revenue_at_risk"].max()
    priority_segments["retention_priority_score"] = 100 * priority_segments["revenue_at_risk"] / max_revenue
    priority_segments["segment"] = priority_segments[["contract", "payment_method", "internet_service"]].agg(" | ".join, axis=1)
    priority_segments["churn_risk"] = pd.cut(
        priority_segments["avg_churn_probability"], bins=[-0.01, 0.40, 0.70, 0.85, 1.0],
        labels=["Low", "Medium", "High", "Very high"],
    )
    priority_segments["revenue_impact"] = pd.cut(
        priority_segments["revenue_at_risk"], bins=[-0.01, max_revenue * 0.33, max_revenue * 0.66, float("inf")],
        labels=["Low", "Medium", "High"], include_lowest=True,
    )
    priority_segments["priority"] = pd.cut(
        priority_segments["retention_priority_score"], bins=[-0.01, 30, 60, 100],
        labels=["P3", "P2", "P1"], include_lowest=True,
    )
    priority_segments["suggested_action"] = priority_segments.apply(
        lambda row: "Contract upgrade discount" if row["contract"] == "Month-to-month"
        else "Proactive engagement campaign", axis=1,
    )
    priority_display = priority_segments.nlargest(10, "revenue_at_risk")[[
        "segment", "churn_risk", "revenue_impact", "priority", "high_risk_customer_count",
        "revenue_at_risk", "estimated_saved_revenue", "suggested_action",
    ]]
    st.dataframe(priority_display, hide_index=True, use_container_width=True, column_config={
        "revenue_at_risk": st.column_config.NumberColumn(format="$%.2f"),
        "estimated_saved_revenue": st.column_config.NumberColumn(format="$%.2f"),
    })

with segments_tab:
    st.subheader("Segment churn performance")
    choice = st.radio("Segment", ["Contract", "Payment method", "Internet service"], horizontal=True)
    frame, label = {
        "Contract": (data["contract"], "contract"),
        "Payment method": (data["payment"], "payment_method"),
        "Internet service": (data["internet"], "internet_service"),
    }[choice]
    chart = frame.set_index(label)[["churn_rate"]].rename(columns={"churn_rate": "Churn rate"})
    st.bar_chart(chart, y="Churn rate")
    display = frame.copy()
    display["churn_rate"] = display["churn_rate"].map(lambda x: f"{x:.1%}")
    display["avg_monthly_charges"] = display["avg_monthly_charges"].map(money)
    st.dataframe(display, hide_index=True, use_container_width=True)

with customers_tab:
    st.subheader("Actionable customer queue")
    levels = sorted(risk["risk_level"].dropna().unique())
    selected = st.multiselect("Risk level", levels, default=levels)
    customer_view = risk[risk["risk_level"].isin(selected)].sort_values("churn_probability", ascending=False)
    columns = ["customer_id", "churn_probability", "risk_level", "retention_priority_score", "retention_priority", "monthly_charges", "contract", "payment_method", "recommended_action"]
    st.dataframe(customer_view[columns], hide_index=True, use_container_width=True, column_config={
        "churn_probability": st.column_config.ProgressColumn("Churn probability", min_value=0, max_value=1, format="percent"),
        "monthly_charges": st.column_config.NumberColumn("Monthly charges", format="$%.2f"),
    })

with revenue_tab:
    st.subheader("Revenue-at-risk analysis")
    st.caption("Revenue at Risk = churn probability × monthly charges")
    st.metric("Total estimated monthly revenue at risk", money(risk["revenue_at_risk"].sum()))
    st.metric("Estimated monthly revenue saved", money(risk["estimated_saved_revenue"].sum()), help="Revenue at risk × 20% planning success rate")
    by_contract = risk.groupby("contract", as_index=False).agg(
        customers=("customer_id", "count"), revenue_at_risk=("revenue_at_risk", "sum")
    ).sort_values("revenue_at_risk", ascending=False)
    left, right = st.columns(2)
    left.bar_chart(by_contract.set_index("contract")[["revenue_at_risk"]])
    shown = by_contract.copy()
    shown["revenue_at_risk"] = shown["revenue_at_risk"].map(money)
    right.dataframe(shown, hide_index=True, use_container_width=True)
    st.subheader("Top 20 customers by revenue impact")
    top20 = risk.nlargest(20, "revenue_at_risk")[[
        "customer_id", "churn_probability", "monthly_charges", "revenue_at_risk", "contract", "recommended_action"
    ]]
    st.dataframe(top20, hide_index=True, use_container_width=True, column_config={
        "churn_probability": st.column_config.NumberColumn(format="percent"),
        "monthly_charges": st.column_config.NumberColumn(format="$%.2f"),
        "revenue_at_risk": st.column_config.NumberColumn(format="$%.2f"),
    })

with quality_tab:
    st.subheader("Latest pipeline health")
    counts = data["counts"].iloc[0]
    quality = data["quality"]
    run = data["runs"]
    status = data["quality_status"]
    failed = int(status["failed_quality_checks"].iloc[0]) if not status.empty else None
    completed_at = pd.to_datetime(status["completed_at_utc"].iloc[0], utc=True) if not status.empty else None
    freshness_hours = (pd.Timestamp.now(tz="UTC") - completed_at).total_seconds() / 3600 if completed_at is not None else None
    cols = st.columns(6)
    cols[0].metric("Pipeline status", status["pipeline_status"].iloc[0].upper() if not status.empty else "NOT RECORDED")
    cols[1].metric("Raw rows", f"{counts['bronze_raw_customer_churn']:,}")
    cols[2].metric("Silver rows", f"{counts['silver_clean_customers']:,}")
    cols[3].metric("Fact rows", f"{counts['fact_customer_churn']:,}")
    cols[4].metric("Failed checks", failed if failed is not None else "N/A")
    cols[5].metric("Data age", f"{freshness_hours:.1f}h" if freshness_hours is not None else "N/A")
    if freshness_hours is not None and freshness_hours >= 30:
        st.error(f"STALE DATA: the latest successful pipeline result is {freshness_hours:.1f} hours old (30-hour threshold).")
    elif completed_at is not None:
        st.caption(f"Latest successful completion: {completed_at.isoformat()}")
    if quality.empty:
        st.warning("This warehouse predates persisted quality audits. Rebuild it to populate pipeline status and gate results.")
    else:
        key_checks = quality[quality["check_name"].isin([
            "require_unique_key", "require_non_null", "fact_customer_unique",
            "fact_dimension_referential_integrity", "fact_silver_row_count"
        ])]
        st.dataframe(key_checks[["check_name", "passed", "details", "checked_at_utc"]], hide_index=True, use_container_width=True)
        st.subheader("All checks")
        st.dataframe(quality, hide_index=True, use_container_width=True)
