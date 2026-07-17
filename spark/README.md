# PySpark Gold-Table Pipeline

`build_churn_gold_tables_pyspark.py` is the distributed-data-processing version of
the project’s core Pandas/SQL Gold transformations. It reads the raw Telco churn CSV,
standardizes the required customer fields, removes duplicate customer identifiers,
calculates segment-level KPIs with Spark DataFrames, and writes each result as a
separate analytical dataset.

The default output format is Parquet under `results/spark_gold/`. Parquet preserves
types, supports column pruning and predicate pushdown, and is a more representative
format for production data-lake workloads than a single local CSV.

## Gold tables reproduced

| Output | Grain and purpose |
|---|---|
| `gold_churn_by_contract` | One row per contract type with customer count, churn rate, and average monthly charges |
| `gold_churn_by_payment` | One row per payment method with the same core churn KPIs |
| `gold_high_risk_segments` | Contract × payment method × internet service segments containing at least 20 customers |
| `mart_segment_churn` | Unioned, dashboard-friendly contract, payment, internet-service, and combined-segment metrics |

These definitions are aligned with the local SQLite and PostgreSQL versions so the
outputs can be compared across execution engines.

## Requirements

- Python 3
- A Java runtime compatible with the installed Spark version
- PySpark dependencies from `requirements-spark.txt`

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-spark.txt
```

## Run locally

PySpark can create a local Spark session when invoked with Python:

```bash
python spark/build_churn_gold_tables_pyspark.py
```

The conventional Spark launcher is also supported and is preferred when supplying
cluster configuration:

```bash
spark-submit spark/build_churn_gold_tables_pyspark.py
```

Write CSV directories instead of Parquet:

```bash
python spark/build_churn_gold_tables_pyspark.py --format csv
```

Override the source and output locations:

```bash
spark-submit spark/build_churn_gold_tables_pyspark.py \
  --input data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv \
  --output results/spark_gold
```

## Sample console output

Row counts and absolute paths can vary by input and environment. A successful run
prints messages similar to:

```text
gold_churn_by_contract generated successfully (3 rows): results/spark_gold/gold_churn_by_contract
gold_churn_by_payment generated successfully (4 rows): results/spark_gold/gold_churn_by_payment
gold_high_risk_segments generated successfully (35 rows): results/spark_gold/gold_high_risk_segments
mart_segment_churn generated successfully (45 rows): results/spark_gold/mart_segment_churn
```

Each Spark output is a directory containing Parquet or CSV part files plus Spark’s
`_SUCCESS` marker.

## Why Spark instead of only Pandas?

Pandas is ideal for this project’s current small source file because it is simple,
fast, and easy to debug on one machine. Spark becomes valuable when the same business
logic must process data that no longer fits comfortably in memory or arrives across
many files and partitions.

Spark provides:

- distributed execution across multiple workers;
- lazy query planning and optimized DataFrame transformations;
- fault-tolerant processing of partitioned datasets;
- native Parquet and data-lake integration;
- a migration path from local batch analytics to large-scale scheduled ETL;
- execution patterns commonly used with Hive, HDFS, S3, lakehouses, and cloud Spark services.

The Spark implementation is deliberately supplemental: Pandas/SQLite remains the
quick local workflow, PostgreSQL provides the service-backed warehouse workflow, and
PySpark demonstrates how the Gold transformation layer scales to distributed data.
