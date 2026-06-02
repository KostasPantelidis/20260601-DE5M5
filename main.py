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
    
    # Deduplicate based on core transaction columns
    df_clean = df_log.drop_duplicates(subset=["Books", "Book checkout", "Book Returned", "Customer ID"])
    
    dropped = initial_count - len(df_clean)
    print(f"   [Metric] Duplicate rows removed: {dropped}")
    return df_clean


def naCheck(df_cust: pd.DataFrame, df_log: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Step 3: Checks for and drops missing values (NaNs) in crucial columns."""
    print("-> Running: naCheck")
    
    # Clean customer NAs
    df_cust_clean = df_cust.dropna(subset=["Customer ID"])
    
    # Clean library logs NAs
    df_log_clean = df_log.dropna(subset=["Books", "Customer ID", "Book checkout", "Book Returned"])
    
    return df_cust_clean, df_log_clean


def dataCleaner(df_cust: pd.DataFrame, df_log: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Step 4: Standardizes data types, strips text whitespace, and applies business rules."""
    print("-> Running: dataCleaner")
    
    # Standardize IDs to clean integers
    df_cust["Customer ID"] = df_cust["Customer ID"].astype(int)
    df_log["Customer ID"] = df_log["Customer ID"].astype(int)
    
    # Clean text columns
    df_log["Books"] = df_log["Books"].astype(str).str.strip()
    df_log["Book checkout"] = df_log["Book checkout"].astype(str).str.replace('"', "")
    df_log["Days allowed to borrow"] = df_log["Days allowed to borrow"].astype(str).str.strip().str.lower()
    
    # Convert dates to actual datetime objects
    df_log["Book checkout"] = pd.to_datetime(df_log["Book checkout"], format="%d/%m/%Y", errors="coerce")
    df_log["Book Returned"] = pd.to_datetime(df_log["Book Returned"], format="%d/%m/%Y", errors="coerce")
    
    # Drop rows that failed date parsing
    df_log = df_log.dropna(subset=["Book checkout", "Book Returned"])
    
    # Filter logical timeline constraints (Checkout can't be in the future or after return date)
    df_log = df_log[(df_log["Book checkout"] <= pd.Timestamp("2026-06-01")) & (df_log["Book checkout"] <= df_log["Book Returned"])]
    
    return df_cust, df_log


def dataEnrich(df_log: pd.DataFrame) -> pd.DataFrame:
    """Step 5: Calculates the days between checkout and return, adding it as a new column."""
    print("-> Running: dataEnrich")
    
    # Subtracting timestamps gives a timedelta; .dt.days extracts just the integer number of days
    df_log["Actual Days Borrowed"] = (df_log["Book Returned"] - df_log["Book checkout"]).dt.days
    
    print("   [Enrichment] Successfully calculated and added 'Actual Days Borrowed' column.")
    return df_log


def addToSQL(df_cust: pd.DataFrame, df_log: pd.DataFrame, server: str, db_name: str) -> None:
    """Step 6: Provisions the target database if missing, then writes tables to SQL Server."""
    print(f"-> Running: addToSQL (Target: {db_name})")
    
    # 1. Database Provisioning
    master_url = f"mssql+pyodbc://@{server}/master?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    master_engine = create_engine(master_url)
    
    with master_engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        db_exists = conn.execute(text(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")).fetchone()
        
        if not db_exists:
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"   Database '{db_name}' created successfully.")
            
    # 2. Table Loading
    target_url = f"mssql+pyodbc://@{server}/{db_name}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    target_engine = create_engine(target_url)
    
    df_cust.to_sql(name="Dim_Customers", con=target_engine, if_exists="replace", index=False)
    df_log.to_sql(name="Fact_LibraryLogs", con=target_engine, if_exists="replace", index=False)
    print("   Data successfully written to SQL Server tables!")


if __name__ == "__main__":
    print("=== STARTING SIMPLIFIED DAY 2 PIPELINE ===\n")
    
    # Step 1: Load
    customers, logs = fileLoader(CUSTOMER_CSV_PATH, LOG_CSV_PATH)
    
    # Track initial log size for metric evaluation
    initial_rows = len(logs)
    
    # Step 2: Check duplicates
    logs = duplicateCheck(logs)
    
    # Step 3: Handle null values
    customers, logs = naCheck(customers, logs)
    
    # Step 4: Clean formats and apply data constraints
    customers, logs = dataCleaner(customers, logs)
    
    # Step 5: Enrich data (New Feature)
    logs = dataEnrich(logs)
    
    # Print a quick quality metric update
    final_rows = len(logs)
    print(f"\n[METRIC SUMMARY] Kept {final_rows} out of {initial_rows} log rows (Dropped {initial_rows - final_rows} rows).\n")
    
    # Step 6: Load to SSMS
    addToSQL(customers, logs, SERVER_NAME, NEW_DB_NAME)
    
    print("\n=== PIPELINE RUN COMPLETE ===")