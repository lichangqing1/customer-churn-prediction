# Google Colab Execution Guide

This guide explains how to run the project in Google Colab using the helper script included in the repository.

---

## 1. Clone or upload the project

Option A: clone from GitHub:

```bash
!git clone <your-repository-url>
%cd customer-churn-prediction
```

Option B: upload the ZIP file to Colab, unzip it, and enter the folder:

```bash
!unzip customer-churn-prediction.zip
%cd customer-churn-prediction
```

Confirm that this file exists:

```bash
!ls scripts/build_churn_warehouse.py
```

---

## 2. Run the full Colab helper

The project includes:

```text
scripts/run_colab.py
```

Run the full workflow:

```bash
!python scripts/run_colab.py --install --test --dashboard
```

This command will:

1. install dependencies from `requirements.txt`;
2. run `pytest -q`;
3. build the SQLite warehouse;
4. export the Power BI mart CSV files;
5. start the Streamlit dashboard on port 8501.

Expected final messages:

```text
Colab pipeline completed successfully.
Warehouse: data/warehouse/customer_churn_warehouse.sqlite
Mart exports: results/mart_exports/
Power BI exports: results/powerbi_exports/
```

---

## 3. Open the Streamlit dashboard in Colab

After running with `--dashboard`, execute this in the next Colab cell:

```python
from google.colab import output

dashboard_url = output.eval_js('google.colab.kernel.proxyPort(8501)')
print(dashboard_url)
```

Open the printed URL.

If Streamlit fails to start, inspect:

```bash
!cat streamlit-colab.log
```

---

## 4. Run only the pipeline without dashboard

If you only need the warehouse and Power BI exports:

```bash
!python scripts/run_colab.py --install --test
```

Or if dependencies are already installed:

```bash
!python scripts/run_colab.py --test
```

---

## 5. Manual commands

Instead of the helper script, you can run each step manually:

```bash
!pip install -r requirements.txt
!pytest -q
!python scripts/build_churn_warehouse.py
!python scripts/export_powerbi_data.py
```

Expected Power BI files:

```bash
!ls results/powerbi_exports
```

Expected output:

```text
mart_churn_overview.csv
mart_segment_churn.csv
mart_revenue_at_risk.csv
mart_retention_actions.csv
mart_data_quality_status.csv
```

---

## 6. Optional PySpark run

Install Spark dependencies and run the Spark Gold-table transformation:

```bash
!python scripts/run_colab.py --install --spark
```

Or manually:

```bash
!pip install -r requirements-spark.txt
!python spark/build_churn_gold_tables_pyspark.py
```

Expected output directory:

```text
results/spark_gold/
```

---

## 7. Common Colab issues

### Project root not found

Use:

```bash
!python scripts/run_colab.py --project-root /content/customer-churn-prediction --install --test
```

### Streamlit site cannot be reached

In Colab, do not open `localhost:8501` directly. Use the Colab proxy:

```python
from google.colab import output
print(output.eval_js('google.colab.kernel.proxyPort(8501)'))
```

### Streamlit process already running

Stop old Streamlit processes:

```bash
!pkill -f streamlit
```

Then launch again:

```bash
!python scripts/run_colab.py --dashboard
```

### Power BI cannot run in Colab

Power BI Desktop is a Windows desktop application. In Colab, generate the CSV files, then download the `results/powerbi_exports/` folder and import those CSV files into Power BI Desktop on Windows.

---

## 8. Files generated in Colab

The main generated files are:

```text
data/warehouse/customer_churn_warehouse.sqlite
results/mart_exports/*.csv
results/powerbi_exports/*.csv
results/spark_gold/       # only if Spark is used
```

These are runtime artifacts and are not required to be committed to GitHub.
