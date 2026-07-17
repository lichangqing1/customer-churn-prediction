import pandas as pd


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to lowercase and replace spaces with underscores.
    """
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df


def rename_telco_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename Telco Customer Churn dataset columns into cleaner snake_case names.
    """
    df = df.copy()

    rename_map = {
        "customerid": "customer_id",
        "seniorcitizen": "senior_citizen",
        "phoneservice": "phone_service",
        "multiplelines": "multiple_lines",
        "internetservice": "internet_service",
        "onlinesecurity": "online_security",
        "onlinebackup": "online_backup",
        "deviceprotection": "device_protection",
        "techsupport": "tech_support",
        "streamingtv": "streaming_tv",
        "streamingmovies": "streaming_movies",
        "paperlessbilling": "paperless_billing",
        "paymentmethod": "payment_method",
        "monthlycharges": "monthly_charges",
        "totalcharges": "total_charges"
    }

    return df.rename(columns=rename_map)


def clean_total_charges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert total_charges to numeric and fill missing values with median.
    """
    df = df.copy()

    if "total_charges" not in df.columns:
        raise KeyError("Column 'total_charges' not found. Please rename columns first.")

    df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")
    df["total_charges"] = df["total_charges"].fillna(df["total_charges"].median())

    return df


def encode_churn_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode churn target:
    Yes -> 1
    No  -> 0
    """
    df = df.copy()

    if "churn" not in df.columns:
        raise KeyError("Column 'churn' not found.")

    df["churn_flag"] = df["churn"].map({"Yes": 1, "No": 0})

    return df


def check_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return missing value count and percentage for each column.
    """
    return pd.DataFrame({
        "missing_count": df.isnull().sum(),
        "missing_percent": df.isnull().mean() * 100
    }).sort_values("missing_percent", ascending=False)


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicated rows.
    """
    return df.drop_duplicates()


def prepare_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline for the Telco Customer Churn dataset.
    """
    df = standardize_column_names(df)
    df = rename_telco_columns(df)
    df = clean_total_charges(df)
    df = encode_churn_target(df)
    df = remove_duplicates(df)

    return df


def validate_clean_data(df: pd.DataFrame) -> None:
    """
    Validate that the cleaned dataset has key columns and valid target values.
    """
    required_columns = [
        "customer_id",
        "tenure",
        "monthly_charges",
        "total_charges",
        "contract",
        "payment_method",
        "churn",
        "churn_flag"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if df["churn_flag"].isnull().sum() > 0:
        raise ValueError("churn_flag contains missing values.")

    if not df["churn_flag"].isin([0, 1]).all():
        raise ValueError("churn_flag must only contain 0 and 1.")

    print("Cleaned data validation passed.")
