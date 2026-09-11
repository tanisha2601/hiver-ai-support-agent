"""
Conversation reconstruction and brand metrics analysis for TWCS dataset.
Reconstructs conversation threads from reply relationships (tweet_id, response_tweet_id, in_response_to_tweet_id)
and calculates comparative metrics for candidate customer support brands.
"""

import os
import glob
import time
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

def find_dataset(raw_dir: str = "data/raw") -> Optional[str]:
    """Finds the first CSV or TSV file in the specified directory."""
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    tsv_files = glob.glob(os.path.join(raw_dir, "*.tsv"))
    all_files = csv_files + tsv_files
    if not all_files:
        return None
    return all_files[0]

def parse_twitter_dates(date_series: pd.Series) -> pd.Series:
    """Parses Twitter-formatted date strings efficiently and without warnings."""
    return pd.to_datetime(date_series, format='%a %b %d %H:%M:%S %z %Y', errors='coerce')

def load_twcs_data(file_path: str, usecols: Optional[List[str]] = None) -> pd.DataFrame:
    """Loads TWCS dataset efficiently."""
    if usecols is None:
        usecols = [
            'tweet_id', 'author_id', 'inbound', 'created_at',
            'text', 'response_tweet_id', 'in_response_to_tweet_id'
        ]
    df = pd.read_csv(
        file_path,
        usecols=usecols,
        low_memory=False,
        dtype={
            'tweet_id': 'int64',
            'author_id': 'string',
            'inbound': 'boolean',
            'text': 'string',
            'response_tweet_id': 'string'
        }
    )
    return df

def reconstruct_conversation_trees(df: pd.DataFrame) -> Tuple[Dict[int, int], Dict[int, List[int]]]:
    """
    Reconstructs conversation trees from parent reply relationships.
    Returns:
      - tweet_to_root: dict mapping tweet_id -> root tweet_id (conversation_id)
      - conv_to_tweets: dict mapping root tweet_id -> list of tweet_ids in thread
    """
    tweet_ids = df['tweet_id'].to_numpy()
    in_reply_to = df['in_response_to_tweet_id'].to_numpy()
    
    id_set = set(tweet_ids)
    parent_map = {}
    for tid, pid in zip(tweet_ids, in_reply_to):
        if not np.isnan(pid):
            pid_int = int(pid)
            if pid_int in id_set:
                parent_map[tid] = pid_int

    root_memo = {}
    def get_root(tid: int) -> int:
        path = []
        curr = tid
        while curr in parent_map:
            if curr in root_memo:
                curr = root_memo[curr]
                break
            path.append(curr)
            curr = parent_map[curr]
            if curr in path:  # guard against potential cyclic loops
                break
        for node in path:
            root_memo[node] = curr
        return curr

    tweet_to_root = {}
    conv_to_tweets = defaultdict(list)
    for tid in tweet_ids:
        r = get_root(tid)
        tweet_to_root[tid] = r
        conv_to_tweets[r].append(tid)

    return tweet_to_root, conv_to_tweets

def compute_brand_metrics(df: pd.DataFrame, brands: List[str]) -> pd.DataFrame:
    """
    Computes all 15 conversation and relationship metrics for specified candidate brands.
    """
    print("Reconstructing conversation graph...")
    t0 = time.time()
    tweet_to_root, conv_to_tweets = reconstruct_conversation_trees(df)
    print(f"Graph reconstructed in {time.time() - t0:.2f}s across {len(df)} tweets and {len(conv_to_tweets)} conversations.")

    # Build fast lookup arrays
    tweet_ids = df['tweet_id'].to_numpy()
    author_ids = df['author_id'].to_numpy()
    inbounds = df['inbound'].to_numpy()
    in_reply_to = df['in_response_to_tweet_id'].to_numpy()
    texts = df['text'].to_numpy()
    created_ats = df['created_at'].to_numpy()

    id_to_idx = {tid: i for i, tid in enumerate(tweet_ids)}
    
    # Pre-parse valid parent links
    # parent_idx_map: idx -> parent_idx
    parent_idx_map = {}
    for i, pid in enumerate(in_reply_to):
        if not np.isnan(pid):
            pid_int = int(pid)
            if pid_int in id_to_idx:
                parent_idx_map[i] = id_to_idx[pid_int]

    results = []

    for brand in brands:
        print(f"Analyzing brand: {brand}...")
        brand_mask = (author_ids == brand)
        brand_indices = np.where(brand_mask)[0]
        brand_tids = tweet_ids[brand_indices]

        # 1. Total brand messages (outbound)
        total_brand_messages = len(brand_tids)

        # Find all conversations where this brand participated
        brand_conv_roots = set()
        for tid in brand_tids:
            brand_conv_roots.add(tweet_to_root[tid])
        
        # All tweet indices belonging to these brand conversations
        brand_conv_tweet_ids = []
        for r in brand_conv_roots:
            brand_conv_tweet_ids.extend(conv_to_tweets[r])
        
        brand_conv_indices = [id_to_idx[tid] for tid in brand_conv_tweet_ids]

        # 2. Customer / inbound messages associated with the brand
        # Inbound messages belonging to conversations involving the brand
        inbound_conv_indices = [idx for idx in brand_conv_indices if inbounds[idx] == True]
        total_customer_inbound = len(inbound_conv_indices)

        # 3. Brand / outbound messages
        outbound_messages = total_brand_messages

        # 4. Direct customer -> brand reply relationships
        # (Brand message replying directly to an inbound customer message)
        cust_to_brand_links = 0
        customer_tids_with_brand_reply = set()
        for b_idx in brand_indices:
            if b_idx in parent_idx_map:
                p_idx = parent_idx_map[b_idx]
                if inbounds[p_idx] == True:
                    cust_to_brand_links += 1
                    customer_tids_with_brand_reply.add(tweet_ids[p_idx])

        # 5. Direct brand -> customer reply relationships
        # (Customer inbound message replying directly to a brand outbound message)
        brand_to_cust_links = 0
        for c_idx in inbound_conv_indices:
            if c_idx in parent_idx_map:
                p_idx = parent_idx_map[c_idx]
                if author_ids[p_idx] == brand:
                    brand_to_cust_links += 1

        # 6. Number of conversations containing both customer and brand messages
        convs_both_sides = 0
        conv_lengths = []
        conv_with_at_least_2 = 0

        for r in brand_conv_roots:
            tids_in_c = conv_to_tweets[r]
            length = len(tids_in_c)
            conv_lengths.append(length)
            if length >= 2:
                conv_with_at_least_2 += 1
            
            has_brand = any(author_ids[id_to_idx[t]] == brand for t in tids_in_c)
            has_cust = any(inbounds[id_to_idx[t]] == True for t in tids_in_c)
            if has_brand and has_cust:
                convs_both_sides += 1

        # 7. Customer messages that received a brand response
        cust_messages_with_response = len(customer_tids_with_brand_reply)

        # 8. Response coverage rate
        # Denominator: Total inbound customer messages in conversations involving the brand
        response_coverage_pct = (cust_messages_with_response / total_customer_inbound * 100) if total_customer_inbound > 0 else 0.0

        # 9. Average conversation length
        avg_conv_length = float(np.mean(conv_lengths)) if conv_lengths else 0.0

        # 10. Median conversation length
        median_conv_length = float(np.median(conv_lengths)) if conv_lengths else 0.0

        # 11. Maximum conversation length
        max_conv_length = int(np.max(conv_lengths)) if conv_lengths else 0

        # 12. Percentage of conversations containing at least 2 messages
        pct_conv_at_least_2 = (conv_with_at_least_2 / len(brand_conv_roots) * 100) if brand_conv_roots else 0.0

        # 13. Percentage of customer messages with usable previous context
        # A customer message has usable previous context if it has a valid parent in the conversation thread
        cust_with_context = 0
        for idx in inbound_conv_indices:
            if idx in parent_idx_map:
                cust_with_context += 1
        pct_cust_with_context = (cust_with_context / total_customer_inbound * 100) if total_customer_inbound > 0 else 0.0

        # 14. Date range of usable conversations
        brand_dates = [created_ats[idx] for idx in brand_conv_indices]
        parsed_dates = parse_twitter_dates(pd.Series(brand_dates))
        min_date = parsed_dates.min()
        max_date = parsed_dates.max()
        date_range_str = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"

        # 15. Usable customer-support examples after removing empty/invalid text
        # Check text quality: non-empty, length > 5, not null
        usable_examples = 0
        for idx in brand_conv_indices:
            txt = texts[idx]
            if pd.notna(txt) and len(str(txt).strip()) > 5:
                usable_examples += 1

        results.append({
            'Brand': brand,
            'Total Messages (Brand)': total_brand_messages,
            'Customer Inbound Messages': total_customer_inbound,
            'Brand Outbound Messages': outbound_messages,
            'Customer->Brand Links': cust_to_brand_links,
            'Brand->Customer Links': brand_to_cust_links,
            'Conversations With Both Sides': convs_both_sides,
            'Cust Messages With Brand Reply': cust_messages_with_response,
            'Response Coverage (%)': round(response_coverage_pct, 2),
            'Avg Conv Length': round(avg_conv_length, 2),
            'Median Conv Length': round(median_conv_length, 2),
            'Max Conv Length': max_conv_length,
            'Conv >= 2 Msgs (%)': round(pct_conv_at_least_2, 2),
            'Cust Msgs With Context (%)': round(pct_cust_with_context, 2),
            'Date Range': date_range_str,
            'Usable Messages Count': usable_examples,
            'Total Conversations': len(brand_conv_roots)
        })

    return pd.DataFrame(results)

def extract_conversation_samples(
    df: pd.DataFrame,
    brand: str,
    output_path: str = "data/processed/conversation_sample.csv",
    sample_size: int = 50
) -> pd.DataFrame:
    """
    Extracts a representative sample of reconstructed multi-turn conversations for a brand.
    Saves to CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tweet_to_root, conv_to_tweets = reconstruct_conversation_trees(df)

    brand_mask = (df['author_id'] == brand)
    brand_tids = df.loc[brand_mask, 'tweet_id'].to_numpy()

    # Find conversations with both brand and customer, length >= 2
    author_map = dict(zip(df['tweet_id'], df['author_id']))
    inbound_map = dict(zip(df['tweet_id'], df['inbound']))
    text_map = dict(zip(df['tweet_id'], df['text']))
    created_at_map = dict(zip(df['tweet_id'], df['created_at']))
    parent_map = dict(zip(df['tweet_id'], df['in_response_to_tweet_id']))

    candidate_convs = []
    brand_roots = {tweet_to_root[tid] for tid in brand_tids}

    for r in brand_roots:
        tids = conv_to_tweets[r]
        if len(tids) >= 2:
            has_brand = any(author_map.get(t) == brand for t in tids)
            has_cust = any(inbound_map.get(t) == True for t in tids)
            if has_brand and has_cust:
                candidate_convs.append(r)

    # Sort or sample deterministically
    np.random.seed(42)
    selected_roots = np.random.choice(candidate_convs, size=min(sample_size, len(candidate_convs)), replace=False)

    rows = []
    for conv_id, r in enumerate(selected_roots, 1):
        tids = conv_to_tweets[r]
        
        parsed_items = []
        for tid in tids:
            parsed_items.append({
                'conversation_id': conv_id,
                'root_tweet_id': r,
                'tweet_id': tid,
                'author_id': author_map.get(tid),
                'inbound': inbound_map.get(tid),
                'created_at': created_at_map.get(tid),
                'in_response_to_tweet_id': parent_map.get(tid),
                'text': text_map.get(tid)
            })
        
        # Sort chronologically
        parsed_items.sort(key=lambda x: str(x['created_at']))
        for turn_idx, item in enumerate(parsed_items, 1):
            item['turn_index'] = turn_idx
            rows.append(item)

    sample_df = pd.DataFrame(rows)
    sample_df.to_csv(output_path, index=False)
    print(f"Saved {len(sample_df)} turns across {len(selected_roots)} conversations to {output_path}")
    return sample_df

def main():
    file_path = find_dataset()
    if not file_path:
        print("No dataset found in data/raw/.")
        return

    print(f"Loading dataset from {file_path}...")
    df = load_twcs_data(file_path)
    print(f"Loaded {len(df)} records.")

    candidate_brands = [
        'AmazonHelp',
        'AppleSupport',
        'Uber_Support',
        'SpotifyCares',
        'Delta'
    ]

    metrics_df = compute_brand_metrics(df, candidate_brands)
    print("\n" + "="*80)
    print("STEP 3 — CANDIDATE BRAND CONVERSATION RECONSTRUCTION COMPARISON")
    print("="*80)
    print(metrics_df.to_string(index=False))

    # Save summary metrics to csv for record
    os.makedirs("results", exist_ok=True)
    metrics_df.to_csv("results/brand_reconstruction_metrics.csv", index=False)
    print("\nSaved metrics to results/brand_reconstruction_metrics.csv")

    # Extract sample conversations for the candidate brands
    extract_conversation_samples(df, brand='AppleSupport', output_path='data/processed/conversation_sample.csv', sample_size=50)

if __name__ == "__main__":
    main()
