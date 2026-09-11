import os
import glob
import pandas as pd
from typing import Optional

def find_dataset(raw_dir: str = "data/raw") -> Optional[str]:
    """Finds the first CSV or TSV file in the specified directory."""
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    tsv_files = glob.glob(os.path.join(raw_dir, "*.tsv"))
    all_files = csv_files + tsv_files
    
    if not all_files:
        return None
    return all_files[0]

def analyze_dataset(file_path: str):
    """Loads and analyzes the dataset, printing relevant statistics."""
    print(f"--- Dataset Analysis ---")
    print(f"File: {file_path}")
    
    # Load dataset safely
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, low_memory=False)
        else:
            df = pd.read_csv(file_path, sep='\t', low_memory=False)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # Basic Info
    rows, cols = df.shape
    print(f"\nShape: {rows} rows, {cols} columns")
    print(f"Memory Usage: {df.memory_usage(deep=True).sum() / (1024 ** 2):.2f} MB")
    
    print("\nColumns and Data Types:")
    for col, dtype in df.dtypes.items():
        print(f" - {col}: {dtype}")

    # Missing Values
    print("\nMissing Values:")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    for col in df.columns:
        if missing[col] > 0:
            print(f" - {col}: {missing[col]} ({missing_pct[col]:.2f}%)")
        else:
            print(f" - {col}: 0 (0.00%)")

    # Duplicates
    duplicates = df.duplicated().sum()
    print(f"\nDuplicate Rows: {duplicates}")

    # Sample
    print("\nSample Data (First 3 rows):")
    print(df.head(3).to_string())

    # Identify potential columns based on names/content
    tweet_id_col = next((c for c in df.columns if 'tweet_id' in c.lower() or 'id' in c.lower()), None)
    author_id_col = next((c for c in df.columns if 'author' in c.lower() or 'user' in c.lower()), None)
    response_col = next((c for c in df.columns if 'response_tweet_id' in c.lower() or 'in_response_to' in c.lower()), None)
    text_col = next((c for c in df.columns if 'text' in c.lower() or 'message' in c.lower() or 'content' in c.lower()), None)
    inbound_col = next((c for c in df.columns if 'inbound' in c.lower() or 'outbound' in c.lower()), None)
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'created' in c.lower()), None)

    print("\nDetected Columns:")
    print(f" - Tweet ID: {tweet_id_col}")
    print(f" - Author ID: {author_id_col}")
    print(f" - Response Relationship: {response_col}")
    print(f" - Message Text: {text_col}")
    print(f" - Inbound/Outbound Status: {inbound_col}")
    print(f" - Timestamp/Date: {date_col}")

    # Analyze Inbound/Outbound
    if inbound_col:
        print("\nInbound/Outbound Distribution:")
        print(df[inbound_col].value_counts(dropna=False).to_string())

    # Analyze Date
    if date_col:
        try:
            dates = pd.to_datetime(df[date_col], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
            print(f"\nDate Range: {dates.min()} to {dates.max()}")
        except Exception as e:
            print(f"\nCould not parse dates: {e}")

    # Unique Brands
    if author_id_col:
        unique_authors = df[author_id_col].nunique()
        print(f"\nUnique Authors/Brands: {unique_authors}")

if __name__ == "__main__":
    file_path = find_dataset()
    if file_path:
        analyze_dataset(file_path)
    else:
        print("No dataset found in data/raw/. Please download the 'Customer Support on Twitter' dataset and place the CSV file in data/raw/.")
