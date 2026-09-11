import pandas as pd
from typing import Optional
from src.data.analyze_dataset import find_dataset

def analyze_brands(file_path: str):
    """Analyzes the dataset to extract brand-specific conversation metrics."""
    print(f"--- Brand Analysis ---")
    
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, low_memory=False)
        else:
            df = pd.read_csv(file_path, sep='\t', low_memory=False)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    author_id_col = next((c for c in df.columns if 'author' in c.lower() or 'user' in c.lower()), None)
    inbound_col = next((c for c in df.columns if 'inbound' in c.lower()), None)
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'created' in c.lower()), None)
    
    if not author_id_col:
        print("Author ID column not found. Cannot perform brand analysis.")
        return

    print(f"Total Messages: {len(df)}")
    
    if inbound_col:
        # For candidate brands/accounts, let's analyze top 5 by volume
        top_authors = df[author_id_col].value_counts().head(5).index
        print(f"\nAnalyzing top 5 authors by message volume: {list(top_authors)}")
        
        for author in top_authors:
            author_df = df[df[author_id_col] == author]
            total = len(author_df)
            inbound_count = author_df[author_df[inbound_col] == True].shape[0] if inbound_col else "Unknown"
            outbound_count = author_df[author_df[inbound_col] == False].shape[0] if inbound_col else "Unknown"
            
            print(f"\nBrand/Author: {author}")
            print(f" - Total Messages: {total}")
            print(f" - Inbound Messages: {inbound_count}")
            print(f" - Outbound Messages: {outbound_count}")
            
            if date_col:
                try:
                    dates = pd.to_datetime(author_df[date_col], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
                    print(f" - Date Range: {dates.min()} to {dates.max()}")
                except:
                    pass
            
    print("\nNote: Conversation reconstruction (unique conversations, median messages per conv, % with context) requires linking tweet IDs with response IDs.")
    print("These metrics will be calculated fully when relationship mapping is established.")

if __name__ == "__main__":
    file_path = find_dataset()
    if file_path:
        analyze_brands(file_path)
    else:
        print("No dataset found in data/raw/. Please place the dataset file first.")
