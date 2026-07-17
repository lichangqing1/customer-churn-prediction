"""Run the customer-churn project end to end in Google Colab.

Run from a Colab cell after cloning or uploading the repository:
    !python scripts/run_colab.py --install --test --dashboard
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    print(f"\n$ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def find_project_root(explicit: str | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend([Path.cwd(), Path("/content/customer-churn-prediction")])
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if (resolved / "scripts/build_churn_warehouse.py").is_file():
            return resolved
    raise FileNotFoundError(
        "Project root not found. Clone/upload the repository, then pass --project-root."
    )


def install_dependencies(root: Path, include_spark: bool) -> None:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], root)
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], root)
    if include_spark:
        run([sys.executable, "-m", "pip", "install", "-r", "requirements-spark.txt"], root)


def launch_dashboard(root: Path) -> None:
    """Start Streamlit; the notebook cell must request the Colab proxy URL."""
    log_path = root / "streamlit-colab.log"
    log_file = log_path.open("w", encoding="utf-8")
    command = [
        sys.executable, "-m", "streamlit", "run", "dashboard/app.py",
        "--server.address=0.0.0.0", "--server.port=8501",
        "--server.headless=true", "--browser.gatherUsageStats=false",
    ]
    process = subprocess.Popen(
        command, cwd=root, stdout=log_file, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    time.sleep(5)
    if process.poll() is not None:
        log_file.close()
        raise RuntimeError(f"Streamlit failed to start. See {log_path}")
    print(f"\nDashboard process: {process.pid}")
    print(f"Streamlit log: {log_path}")
    print("Streamlit is listening on port 8501.")
    print("Run this in the NEXT COLAB NOTEBOOK CELL to open it:")
    print("from google.colab import output")
    print("dashboard_url = output.eval_js('google.colab.kernel.proxyPort(8501)')")
    print("print(dashboard_url)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", help="Repository location; defaults to cwd or /content/customer-churn-prediction")
    parser.add_argument("--install", action="store_true", help="Install main project requirements")
    parser.add_argument("--test", action="store_true", help="Run pytest before building")
    parser.add_argument("--spark", action="store_true", help="Install PySpark when --install is used and build Spark Gold outputs")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit and print a Colab proxy URL")
    args = parser.parse_args()

    root = find_project_root(args.project_root)
    os.chdir(root)
    print(f"Project root: {root}")
    if args.install:
        install_dependencies(root, args.spark)
    if args.test:
        run([sys.executable, "-m", "pytest", "-q"], root)

    run([sys.executable, "scripts/build_churn_warehouse.py"], root)
    run([sys.executable, "scripts/export_powerbi_data.py"], root)
    if args.spark:
        run([sys.executable, "spark/build_churn_gold_tables_pyspark.py"], root)
    if args.dashboard:
        launch_dashboard(root)

    print("\nColab pipeline completed successfully.")
    print("Warehouse: data/warehouse/customer_churn_warehouse.sqlite")
    print("Mart exports: results/mart_exports/")
    print("Power BI exports: results/powerbi_exports/")
    if args.spark:
        print("Spark Gold outputs: results/spark_gold/")


if __name__ == "__main__":
    main()
