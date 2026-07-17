"""Build churn Gold tables with PySpark and write partition-friendly Parquet outputs."""
from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, functions as F, types as T

ROOT = Path(__file__).resolve().parents[1]


def prepare_customer_snapshot(raw: DataFrame) -> DataFrame:
    """Standardize the Telco source fields required by the Gold transformations."""
    return (
        raw.select(
            F.col("customerID").alias("customer_id"),
            F.col("Contract").alias("contract"),
            F.col("PaymentMethod").alias("payment_method"),
            F.col("InternetService").alias("internet_service"),
            F.col("MonthlyCharges").cast(T.DoubleType()).alias("monthly_charges"),
            F.when(F.col("Churn") == "Yes", 1).when(F.col("Churn") == "No", 0).alias("churn_flag"),
        )
        .dropDuplicates(["customer_id"])
        .filter(F.col("customer_id").isNotNull())
    )


def aggregate_segment(customers: DataFrame, dimensions: list[str]) -> DataFrame:
    return (
        customers.groupBy(*dimensions)
        .agg(
            F.countDistinct("customer_id").alias("customers"),
            F.avg("churn_flag").alias("churn_rate"),
            F.avg("monthly_charges").alias("avg_monthly_charges"),
        )
    )


def build_gold_tables(customers: DataFrame) -> dict[str, DataFrame]:
    """Return Gold outputs with definitions aligned to the SQLite/PostgreSQL marts."""
    by_contract = aggregate_segment(customers, ["contract"])
    by_payment = aggregate_segment(customers, ["payment_method"])
    high_risk = (
        aggregate_segment(customers, ["contract", "payment_method", "internet_service"])
        .filter(F.col("customers") >= 20)
    )

    segment_frames = []
    for segment_type, column in (
        ("contract", "contract"),
        ("payment_method", "payment_method"),
        ("internet_service", "internet_service"),
    ):
        segment_frames.append(
            aggregate_segment(customers, [column]).select(
                F.lit(segment_type).alias("segment_type"),
                F.col(column).alias("segment_value"),
                "customers", "churn_rate", "avg_monthly_charges",
            )
        )
    combined = high_risk.select(
        F.lit("combined_risk_segment").alias("segment_type"),
        F.concat_ws(" | ", "contract", "payment_method", "internet_service").alias("segment_value"),
        "customers", "churn_rate", "avg_monthly_charges",
    )
    mart_segment = segment_frames[0].unionByName(segment_frames[1]).unionByName(
        segment_frames[2]
    ).unionByName(combined)
    return {
        "gold_churn_by_contract": by_contract,
        "gold_churn_by_payment": by_payment,
        "gold_high_risk_segments": high_risk,
        "mart_segment_churn": mart_segment,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "results/spark_gold")
    parser.add_argument("--format", choices=("parquet", "csv"), default="parquet")
    args = parser.parse_args()
    spark = SparkSession.builder.appName("customer-churn-gold-tables").getOrCreate()
    try:
        raw = spark.read.option("header", True).option("inferSchema", True).csv(str(args.input))
        customers = prepare_customer_snapshot(raw).cache()
        tables = build_gold_tables(customers)
        for name, frame in tables.items():
            row_count = frame.count()
            output_path = args.output / name
            writer = frame.orderBy(F.desc("churn_rate")).coalesce(1).write.mode("overwrite")
            if args.format == "csv":
                writer.option("header", True).csv(str(output_path))
            else:
                writer.parquet(str(output_path))
            print(f"{name} generated successfully ({row_count} rows): {output_path}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
