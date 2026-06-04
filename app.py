import os
import time
from datetime import datetime
import pandas as pd

def run_pipeline():
    print("Starting Library Data Quality Pipeline...")
    start_time = time.time()

    # Define paths
    data_dir = "data"
    output_dir = "output"

    customer_path   = os.path.join(data_dir, "03_Library SystemCustomers.csv")
    borrowings_path = os.path.join(data_dir, "03_Library Systembook.csv")
    results_path            = os.path.join(output_dir, "results.csv")
    cleaned_borrowings_path = os.path.join(output_dir, "cleaned_borrowings.csv")

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(customer_path) or not os.path.exists(borrowings_path):
        print("Error: Source CSV files missing from 'data/' directory.")
        return

    # ==========================================
    # 1. INGESTION & HEADER NORMALIZATION
    # ==========================================
    print("Ingesting source datasets...")
    df_customers  = pd.read_csv(customer_path)
    df_borrowings = pd.read_csv(borrowings_path)

    df_customers.columns  = df_customers.columns.str.strip().str.lower()
    df_borrowings.columns = df_borrowings.columns.str.strip().str.lower()

    total_raw_records = len(df_customers) + len(df_borrowings)

    # ==========================================
    # 2. CLEANING & TRANSFORMATION
    # ==========================================
    print("Cleaning data issues...")

    # --- Clean Customers ---
    if 'customer id' in df_customers.columns:
        df_customers_clean = df_customers.drop_duplicates(subset=['customer id']).copy()
    else:
        df_customers_clean = df_customers.drop_duplicates().copy()

    if 'customer name' in df_customers_clean.columns:
        df_customers_clean['customer name'] = df_customers_clean['customer name'].fillna("Unknown Customer")

    # --- Clean Borrowings ---
    df_borrowings_clean = df_borrowings.dropna(subset=['id', 'customer id', 'books']).copy()
    df_borrowings_clean = df_borrowings_clean.drop_duplicates()

    # Normalize dates
    for date_col in ['book checkout', 'book returned']:
        if date_col in df_borrowings_clean.columns:
            df_borrowings_clean[date_col] = pd.to_datetime(
                df_borrowings_clean[date_col], errors='coerce'
            )

    # Referential integrity — capture drop count before filtering
    pre_referential_count = len(df_borrowings_clean)
    if 'customer id' in df_customers_clean.columns and 'customer id' in df_borrowings_clean.columns:
        valid_ids = df_customers_clean['customer id'].unique()
        df_borrowings_clean = df_borrowings_clean[
            df_borrowings_clean['customer id'].isin(valid_ids)
        ]
    referential_integrity_drops = pre_referential_count - len(df_borrowings_clean)

    # ==========================================
    # 3. METRICS GATHERING
    # ==========================================
    print("Calculating execution metrics...")

    total_cleaned_records   = len(df_customers_clean) + len(df_borrowings_clean)
    records_dropped         = total_raw_records - total_cleaned_records

    unique_books_count      = df_borrowings_clean['books'].nunique()           if 'books'          in df_borrowings_clean.columns else 0
    unique_customers_count  = df_customers_clean['customer id'].nunique()      if 'customer id'    in df_customers_clean.columns else 0
    missing_dates_count     = df_borrowings_clean['book checkout'].isna().sum() if 'book checkout'  in df_borrowings_clean.columns else 0
    unreturned_books_count  = df_borrowings_clean['book returned'].isna().sum() if 'book returned'  in df_borrowings_clean.columns else 0

    execution_time_seconds = round(time.time() - start_time, 4)

    # ==========================================
    # 4. EXPORT: results.csv  (summary metrics)
    # ==========================================
    metrics_summary = {
        "Execution_Timestamp":              [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Number_of_records_processed":      [total_raw_records],
        "Number_of_records_dropped":        [records_dropped],
        "Unique_Books_Count":               [unique_books_count],
        "Unique_Customers_Count":           [unique_customers_count],
        "Missing_Checkout_Dates_Count":     [missing_dates_count],
        "Unreturned_Books_Count":           [unreturned_books_count],
        "Referential_Integrity_Drops":      [referential_integrity_drops],
        "Pipeline_Execution_Time_Sec":      [execution_time_seconds],
    }

    df_results = pd.DataFrame(metrics_summary)
    df_results.to_csv(results_path, index=False)
    print(f"Summary metrics exported to:    {results_path}")

    # ==========================================
    # 5. EXPORT: cleaned_borrowings.csv  (detail layer for Power BI slicing)
    # ==========================================
    # Merge customer names into the borrowings detail so Power BI
    # has everything it needs in one table (book titles, customer names, dates).
    if 'customer id' in df_customers_clean.columns and 'customer name' in df_customers_clean.columns:
        df_borrowings_clean = df_borrowings_clean.merge(
            df_customers_clean[['customer id', 'customer name']],
            on='customer id',
            how='left'
        )

    df_borrowings_clean.to_csv(cleaned_borrowings_path, index=False)
    print(f"Cleaned borrowings exported to: {cleaned_borrowings_path}")
    print(f"Total Execution Time: {execution_time_seconds} seconds\n")


if __name__ == "__main__":
    run_pipeline()