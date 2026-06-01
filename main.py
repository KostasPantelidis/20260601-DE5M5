import os
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text

# =====================================================================
# GLOBAL CONFIGURATION
# =====================================================================
SERVER_NAME = "localhost"
NEW_DB_NAME = "LibrarySystem_DB"

RAW_CUSTOMER_PATH = (r"C:\Users\Admin\Desktop\20260601-DE5M5\data\03_Library SystemCustomers.csv")
RAW_LOG_PATH = (r"C:\Users\Admin\Desktop\20260601-DE5M5\data\03_Library Systembook.csv")

# This strips out common invisible unicode artifacts (like zero-width spaces)
CUSTOMER_CSV_PATH = (
    RAW_CUSTOMER_PATH.encode("utf-8")
    .decode("utf-8-sig")
    .replace("\u200b", "")
    .strip()
)
LOG_CSV_PATH = (
    RAW_LOG_PATH.encode("utf-8")
    .decode("utf-8-sig")
    .replace("\u200b", "")
    .strip()
)


def extract_data(cust_path: str, log_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reads raw CSV data files into memory."""
    print("--- Step 1: Extracting Raw CSV Data ---")
    if not os.path.exists(cust_path) or not os.path.exists(log_path):
        raise FileNotFoundError(
            "One or both input CSV file paths do not exist. Check your paths!"
        )

    df_cust = pd.read_csv(cust_path)
    df_log = pd.read_csv(log_path)
    return df_cust, df_log


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and standardizes the Customer dataset."""
    print("--- Step 2: Cleaning Customer Dataset ---")
    # Drop completely null rows
    df = df.dropna(how="all")
    # Standardize IDs to clean integers
    df["Customer ID"] = df["Customer ID"].astype(int)
    return df


def clean_library_logs(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans, parses, and validates the Library Logs dataset."""
    print("--- Step 3: Cleaning Library Logs Dataset ---")

    # A. Deduplication (ignoring the arbitrary sequential index column)
    df = df.drop_duplicates(
        subset=["Books", "Book checkout", "Book Returned", "Customer ID"]
    )

    # B. Text & Quotes scrubbing
    df["Books"] = df["Books"].str.strip()
    df["Book checkout"] = (
        df["Book checkout"].astype(str).str.replace('"', "")
    )

    # C. Handle missing critical operational values
    df = df.dropna(subset=["Books", "Customer ID"])
    df["Customer ID"] = df["Customer ID"].astype(int)

    # D. Strict Date Parsing
    df["Book checkout"] = pd.to_datetime(
        df["Book checkout"], format="%d/%m/%Y", errors="coerce"
    )
    df["Book Returned"] = pd.to_datetime(
        df["Book Returned"], format="%d/%m/%Y", errors="coerce"
    )
    df = df.dropna(subset=["Book checkout", "Book Returned"])

    # E. Business Logic & Timeline Constraints
    df = df[
        (df["Book checkout"] <= pd.Timestamp("2026-06-01"))
        & (df["Book checkout"] <= df["Book Returned"])
    ]

    # Standardize string configuration column
    df["Days allowed to borrow"] = (
        df["Days allowed to borrow"].str.strip().str.lower()
    )

    return df


def calculate_metrics(initial_count: int, final_count: int) -> None:
    """Calculates and outputs key pipeline data engineering metrics."""
    dropped_rows = initial_count - final_count
    retention_rate = (
        (final_count / initial_count) * 100 if initial_count > 0 else 0
    )

    print("\n================ DATA QUALITY METRICS ================")
    print(f" Raw Log Records Extracted : {initial_count}")
    print(f" Dirty Records Dropped     : {dropped_rows}")
    print(f" Pipeline Retention Rate   : {retention_rate:.2f}%")
    print("======================================================\n")


def provision_database(server: str, db_name: str) -> None:
    """Connects to system master to automate target database deployment in SSMS."""
    print(f"--- Step 4: Provisioning Target Database on '{server}' ---")
    master_url = f"mssql+pyodbc://@{server}/master?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    master_engine = create_engine(master_url)

    check_db_query = text(
        f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'"
    )

    with master_engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        db_exists = conn.execute(check_db_query).fetchone()

        if not db_exists:
            print(f"   Database '{db_name}' not found. Spawning target DB...")
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"   Database '{db_name}' successfully built.")
        else:
            print(f"   Target database '{db_name}' already exists. Proceeding...")


def load_data_to_ssms(
    df_cust: pd.DataFrame, df_log: pd.DataFrame, server: str, db_name: str
) -> None:
    """Streams dataframes out of memory into finalized target SQL tables."""
    print(f"--- Step 5: Streaming Clean Structures into Database '{db_name}' ---")
    target_url = f"mssql+pyodbc://@{server}/{db_name}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    target_engine = create_engine(target_url)

    # Dump dataframes straight to SQL Server database tables
    df_cust.to_sql(
        name="Dim_Customers", con=target_engine, if_exists="replace", index=False
    )
    print("   Successfully wrote structural table: 'Dim_Customers'")

    df_log.to_sql(
        name="Fact_LibraryLogs",
        con=target_engine,
        if_exists="replace",
        index=False,
    )
    print("   Successfully wrote transaction table: 'Fact_LibraryLogs'")


# =====================================================================
# MAIN PIPELINE ENTRY EXECUTION
# =====================================================================
if __name__ == "__main__":
    print("=== STARTING DATA ENGINEERING LIBRARY PIPELINE ===\n")

    try:
        # 1. Extract
        raw_customers, raw_logs = extract_data(CUSTOMER_CSV_PATH, LOG_CSV_PATH)

        # Cache initial log size for analytics auditing metric step later
        initial_log_volume = len(raw_logs)

        # 2. Transform / Clean
        cleaned_cust_df = clean_customers(raw_customers)
        cleaned_log_df = clean_library_logs(raw_logs)

        # 3. Assess Metric
        calculate_metrics(initial_log_volume, len(cleaned_log_df))

        # 4. Provision & Infrastructure Check
        provision_database(SERVER_NAME, NEW_DB_NAME)

        # 5. Load
        load_data_to_ssms(
            cleaned_cust_df, cleaned_log_df, SERVER_NAME, NEW_DB_NAME
        )

        print("\n=== PIPELINE RUN COMPLETE AND STABLE ===")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Pipeline execution collapsed: {e}")