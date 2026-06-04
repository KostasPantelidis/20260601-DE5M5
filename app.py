import os
import time
from datetime import datetime
import pandas as pd

def run_pipeline():
    print("🚀 Starting Library Data Quality Pipeline...")
    start_time = time.time()
    
    # Define paths
    data_dir = "data"
    output_dir = "output"
    
    customer_path = os.path.join(data_dir, "customer.csv")
    borrowings_path = os.path.join(data_dir, "borrowings.csv")
    results_path = os.path.join(output_dir, "results.csv")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if source files exist
    if not os.path.exists(customer_path) or not os.path.exists(borrowings_path):
        print("❌ Error: Source CSV files missing from 'data/' directory.")
        return

    # ==========================================
    # 1. INGESTION
    # ==========================================
    print("📥 Ingesting source datasets...")
    df_customers = pd.read_csv(customer_path)
    df_borrowings = pd.read_csv(borrowings_path)
    
    # Track initial total records across both files
    total_raw_records = len(df_customers) + len(df_borrowings)
    
    # ==========================================
    # 2. CLEANING & TRANSFORMATION
    # ==========================================
    print("🧹 Cleaning data issues...")
    
    # --- Clean Customers ---
    # Issue: Drop duplicate customer profiles
    df_customers_clean = df_customers.drop_duplicates(subset=['customer_id']).copy()
    # Issue: Handle missing names
    df_customers_clean['customer_name'] = df_customers_clean['customer_name'].fillna("Unknown Customer")
    
    # --- Clean Borrowings ---
    # Issue: Drop rows with completely empty critical fields (like missing book or customer IDs)
    df_borrowings_clean = df_borrowings.dropna(subset=['borrowing_id', 'customer_id', 'book_id']).copy()
    
    # Issue: Deduplicate identical transaction logs
    df_borrowings_clean = df_borrowings_clean.drop_duplicates()
    
    # Issue: Inconsistent date handling
    for date_col in ['checkout_date', 'return_date']:
        if date_col in df_borrowings_clean.columns:
            df_borrowings_clean[date_col] = pd.to_datetime(df_borrowings_clean[date_col], errors='coerce')
            
    # Issue: Referential integrity (Drop customer IDs that don't exist in customer file)
    valid_customer_ids = df_customers_clean['customer_id'].unique()
    df_borrowings_clean = df_borrowings_clean[df_borrowings_clean['customer_id'].isin(valid_customer_ids)]
    
    # ==========================================
    # 3. METRICS GATHERING
    # ==========================================
    print("📊 Calculating execution metrics...")
    
    # Calculate records processed and dropped
    total_cleaned_records = len(df_customers_clean) + len(df_borrowings_clean)
    records_dropped = total_raw_records - total_cleaned_records
    
    # Books & Customer specific counts
    unique_books_count = df_borrowings_clean['book_id'].nunique() if 'book_id' in df_borrowings_clean.columns else 0
    unique_customers_count = df_customers_clean['customer_id'].nunique()
    
    # Pipeline execution time
    execution_time_seconds = round(time.time() - start_time, 4)
    
    # ==========================================
    # 4. GENERATING THE RESULTS CSV
    # ==========================================
    # Structuring data cleanly for Power BI cards and charts
    metrics_summary = {
        "Execution_Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Number_of_records_processed": [total_raw_records],
        "Number_of_records_dropped": [records_dropped],
        "Unique_Books_Count": [unique_books_count],
        "Unique_Customers_Count": [unique_customers_count],
        "Pipeline_Execution_Time_Sec": [execution_time_seconds]
    }
    
    df_results = pd.DataFrame(metrics_summary)
    
    # Write to local csv
    df_results.to_csv(results_path, index=False)
    print(f"💾 Results successfully exported to: {results_path}")
    print(f"⏱️ Total Execution Time: {execution_time_seconds} seconds\n")

if __name__ == "__main__":
    run_pipeline()
