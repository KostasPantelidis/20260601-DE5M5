import os
import pandas as pd
from sqlalchemy import create_engine, text

# =====================================================================
# GLOBAL CONFIGURATION
# =====================================================================
SERVER_NAME = "localhost"
NEW_DB_NAME = "LibrarySystem_DB"

CUSTOMER_CSV_PATH = r"C:\Users\Admin\Desktop\20260601-DE5M5\data\03_Library SystemCustomers.csv"
LOG_CSV_PATH = r"C:\Users\Admin\Desktop\20260601-DE5M5\data\03_Library Systembook.csv"


def fileLoader(cust_path: str, log_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Step 1: Simply reads raw CSV files into pandas dataframes."""
    print("-> Running: fileLoader")
    if not os.path.exists(cust_path) or not os.path.exists(log_path):
        raise FileNotFoundError("Check your file paths! One or both CSVs are missing.")
        
    df_cust = pd.read_csv(cust_path)
    df_log = pd.read_csv(log_path)
    return df_cust, df_log


def duplicateCheck(df_log: pd.DataFrame) -> pd.DataFrame:
    """Step 2: Identifies and removes duplicate records from the library log."""
    print("-> Running: duplicateCheck")
    initial_count = len(df_log)
    df_clean = df_log.drop_duplicates(subset=["Books", "Book checkout", "Book Returned", "Customer ID"])
    dropped = initial_count - len(df_clean)
    print(f"   [Metric] Duplicate rows removed: {dropped}")
    return df_clean


def naCheck(df_cust: pd.DataFrame, df_log: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Step 3: Checks for and drops missing values (NaNs) in crucial columns."""
    print("-> Running: naCheck")
    df_cust_clean = df_cust.dropna(subset=["Customer ID"])
    df_log_clean = df_log.dropna(subset=["Books", "Customer ID", "Book checkout", "Book Returned"])
    return df_cust_clean, df_log_clean


def dataCleaner(df_cust: pd.DataFrame, df_log: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Step 4: Standardizes data types, strips text whitespace."""
    print("-> Running: dataCleaner")
    
    df_cust = df_cust.copy()
    df_log = df_log.copy()

    df_cust["Customer ID"] = df_cust["Customer ID"].astype(int)
    df_log["Customer ID"] = df_log["Customer ID"].astype(int)
    
    df_log["Books"] = df_log["Books"].astype(str).str.strip()
    df_log["Book checkout"] = df_log["Book checkout"].astype(str).str.replace('"', "")
    df_log["Days allowed to borrow"] = df_log["Days allowed to borrow"].astype(str).str.strip().str.lower()
    
    df_log["Book checkout"] = pd.to_datetime(df_log["Book checkout"], format="%d/%m/%Y", errors="coerce")
    df_log["Book Returned"] = pd.to_datetime(df_log["Book Returned"], format="%d/%m/%Y", errors="coerce")
    
    df_log = df_log.dropna(subset=["Book checkout", "Book Returned"])
    
    # Soft max date filter (future dates constraint)
    df_log = df_log[df_log["Book checkout"] <= pd.Timestamp("2026-06-01")]
    
    return df_cust, df_log


def enrich_dateDuration(df: pd.DataFrame, colA: str, colB: str) -> pd.DataFrame:
    """
    Step 5a: Takes two input columns and creates:
    - 'loan_duration': difference in days between colA (Return) and colB (Checkout)
    - 'Checkout_Month': extracted month name from checkout date
    """
    print("-> Running: enrich_dateDuration")
    df = df.copy()
    
    # Calculate duration
    df['loan_duration'] = (df[colA] - df[colB]).dt.days
    
    # Additional requested feature: Month column
    df['Checkout_Month'] = df[colB].dt.strftime('%B')
    
    return df


def filter_valid_loans(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Step 5b: Filters out rows where loan_duration is negative."""
    print("-> Running: filter_valid_loans")
    initial_len = len(df)
    valid_df = df[df['loan_duration'] != 0].copy()
    drop_count = initial_len - len(valid_df)
    print(f"   [Enrichment] Dropped {drop_count} rows due to negative loan durations.")
    return valid_df, drop_count


def addToSQL(df_cust: pd.DataFrame, df_log: pd.DataFrame, server: str, db_name: str) -> None:
    """Step 6: Provisions the target database if missing, then writes tables to SQL Server."""
    print(f"-> Running: addToSQL (Target: {db_name})")
    
    master_url = f"mssql+pyodbc://@{server}/master?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    master_engine = create_engine(master_url)
    
    with master_engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        db_exists = conn.execute(text(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")).fetchone()
        
        if not db_exists:
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"   Database '{db_name}' created successfully.")
            
    target_url = f"mssql+pyodbc://@{server}/{db_name}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    target_engine = create_engine(target_url)
    
    df_cust.to_sql(name="Dim_Customers", con=target_engine, if_exists="replace", index=False)
    df_log.to_sql(name="Fact_LibraryLogs", con=target_engine, if_exists="replace", index=False)
    print("   Data successfully written to SQL Server tables!")


if __name__ == "__main__":
    print("=== STARTING SIMPLIFIED PIPELINE ===\n")
    
    customers, logs = fileLoader(CUSTOMER_CSV_PATH, LOG_CSV_PATH)
    initial_rows = len(logs)
    
    logs = duplicateCheck(logs)
    customers, logs = naCheck(customers, logs)
    customers, logs = dataCleaner(customers, logs)
    
    # Modernized Enrichment steps
    logs = enrich_dateDuration(logs, colA='Book Returned', colB='Book checkout')
    logs, negative_durations_dropped = filter_valid_loans(logs)
    
    final_rows = len(logs)
    print(f"\n[METRIC SUMMARY] Kept {final_rows} out of {initial_rows} log rows.")
    
    addToSQL(customers, logs, SERVER_NAME, NEW_DB_NAME)
    print("\n=== PIPELINE RUN COMPLETE ===")