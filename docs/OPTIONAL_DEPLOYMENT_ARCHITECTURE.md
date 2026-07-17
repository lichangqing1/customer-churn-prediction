# Optional Deployment Architecture

The default project workflow is intentionally local and reproducible: Python builds a SQLite warehouse, SQL creates marts, and Streamlit or exported CSVs provide the presentation layer. The components below are optional extensions that demonstrate deployment and scaling patterns.

## Default local path

```text
Raw CSV → Python pipeline → SQLite warehouse → SQL marts → Streamlit / Power BI exports
```

Run it with:

```bash
python scripts/build_churn_warehouse.py
streamlit run dashboard/app.py
```

This is the recommended path for review, development, and portfolio demonstrations.

## Docker and PostgreSQL

`docker-compose.yml` provides a local multi-service deployment:

```text
Pipeline container → PostgreSQL → Streamlit container
```

Start it with:

```bash
docker compose up --build
```

The pipeline loads warehouse tables and PostgreSQL marts before the dashboard reads them through `DATABASE_URL`. Stop services with `docker compose down`; add `-v` only when the database volume should also be deleted.

This setup demonstrates service separation and database portability. It is not a claim of production hosting, high availability, or automated recovery.

## Airflow scheduling

The DAG in `dags/customer_churn_warehouse_dag.py` represents an optional scheduled workflow:

1. validate the source artifact;
2. build the warehouse;
3. apply marts;
4. verify quality results.

Install Airflow-specific packages from `requirements-airflow.txt`. Airflow is not required for the default build.

## PySpark transformation

`spark/build_churn_gold_tables_pyspark.py` reproduces selected Gold-level aggregations with PySpark and writes generated output beneath `results/spark_gold/`.

```bash
python -m pip install -r requirements-spark.txt
python spark/build_churn_gold_tables_pyspark.py
```

This is a scalability demonstration; pandas and SQL remain the main implementation for this dataset's size.

## Power BI delivery

Power BI consumes CSV exports generated from stable SQL marts:

```bash
python scripts/export_powerbi_data.py
```

For a managed deployment, the same mart contract could be exposed from PostgreSQL or another analytical database. The current repository keeps exports local and reproducible.

## Production boundary

These extensions demonstrate architectural options, not a fully operated production platform. Authentication, secrets management, infrastructure-as-code, monitoring, backups, disaster recovery, and deployment automation would be required before real customer data or business-critical workloads were introduced.

See [Production Readiness](PRODUCTION_READINESS.md) for the explicit capability and gap assessment.
