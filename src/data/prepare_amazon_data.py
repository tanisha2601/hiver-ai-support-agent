"""
Data preparation script for AmazonHelp intent classification.
Filters the TWCS dataset to inbound English messages for AmazonHelp,
preserving conversation structure and removing noise.
"""

import os
import glob
import pandas as pd
import numpy as np
from langdetect import detect, DetectorFactory
from typing import Optional, List

# Ensure deterministic language detection
DetectorFactory.seed = 42

def find_dataset(raw_dir: str = "data/raw") -> Optional[str]:
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    if not csv_files:
        return None
    return csv_files[0]

import re

ENG_STOPWORDS = {'the', 'and', 'to', 'for', 'is', 'in', 'on', 'it', 'this', 'that', 'with', 'have', 'are', 'was', 'my', 'you', 'can', 'not', 'do', 'but'}
NON_ENG_STOPWORDS = {'de', 'que', 'la', 'en', 'un', 'el', 'por', 'para', 'con', 'las', 'los', 'una', 'es', 'yo', 'su', 'se', 'lo', 'como', 'le', 'al', 'o', 'je', 'et', 'les', 'des', 'est', 'pour'}

def is_english(text: str) -> bool:
    if not isinstance(text, str) or len(text.strip()) < 5:
        return False
    
    words = set(re.findall(r'[a-z]+', text.lower()))
    eng_matches = len(words.intersection(ENG_STOPWORDS))
    non_eng_matches = len(words.intersection(NON_ENG_STOPWORDS))
    
    if non_eng_matches > eng_matches:
        return False
    return True

def prepare_data():
    file_path = find_dataset()
    if not file_path:
        print("Raw dataset not found.")
        return

    print("Loading raw dataset...")
    df = pd.read_csv(
        file_path,
        usecols=['tweet_id', 'author_id', 'inbound', 'created_at', 'text', 'in_response_to_tweet_id'],
        dtype={
            'tweet_id': 'int64',
            'author_id': 'string',
            'inbound': 'boolean',
            'text': 'string'
        }
    )
    
    total_raw = len(df)
    print(f"Total raw tweets: {total_raw}")

    # Step 1: Find AmazonHelp conversations
    print("Reconstructing AmazonHelp conversation graph...")
    brand_mask = (df['author_id'] == 'AmazonHelp')
    brand_tids = df.loc[brand_mask, 'tweet_id'].to_numpy()
    
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
            if curr in path:
                break
        for node in path:
            root_memo[node] = curr
        return curr

    tweet_to_root = {}
    from collections import defaultdict
    conv_to_tweets = defaultdict(list)
    
    for tid in tweet_ids:
        r = get_root(tid)
        tweet_to_root[tid] = r
        conv_to_tweets[r].append(tid)

    amazon_roots = set()
    for tid in brand_tids:
        amazon_roots.add(tweet_to_root[tid])
        
    amazon_conv_tids = []
    for r in amazon_roots:
        amazon_conv_tids.extend(conv_to_tweets[r])
        
    amazon_conv_set = set(amazon_conv_tids)
    
    # Filter to AmazonHelp conversation dataset
    amazon_df = df[df['tweet_id'].isin(amazon_conv_set)].copy()
    print(f"AmazonHelp conversation tweets: {len(amazon_df)}")
    
    # Preserve a dictionary of ALL amazon_df texts for context retrieval later
    text_dict = dict(zip(amazon_df['tweet_id'], amazon_df['text']))
    
    # Step 2: Keep only inbound (customer) messages
    inbound_df = amazon_df[amazon_df['inbound'] == True].copy()
    print(f"AmazonHelp inbound customer messages: {len(inbound_df)}")
    
    # Step 3: Text cleaning
    inbound_df['text_clean'] = inbound_df['text'].str.strip()
    inbound_df = inbound_df[inbound_df['text_clean'].str.len() >= 5]
    print(f"After removing short/empty text: {len(inbound_df)}")
    
    # Step 4: Deduplication (same author, same exact text)
    # Sort chronologically so we keep the first instance
    inbound_df['created_at_dt'] = pd.to_datetime(inbound_df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
    inbound_df = inbound_df.sort_values('created_at_dt')
    inbound_df = inbound_df.drop_duplicates(subset=['author_id', 'text_clean'], keep='first')
    print(f"After text deduplication per author: {len(inbound_df)}")
    
    # Step 5: English language filter
    print("Applying langdetect to filter for English (this may take a few minutes)...")
    # To speed up, we can apply langdetect only to non-null strings
    # We will use a fast vectorized approach or standard apply
    is_eng_mask = inbound_df['text_clean'].apply(is_english)
    english_df = inbound_df[is_eng_mask].copy()
    print(f"After English filtering: {len(english_df)}")
    
    # Map previous context for the remaining tweets
    def get_context(pid):
        if pd.isna(pid):
            return None
        return text_dict.get(int(pid), None)
        
    english_df['previous_context'] = english_df['in_response_to_tweet_id'].apply(get_context)
    
    # Add conversation root for grouping later
    english_df['conversation_id'] = english_df['tweet_id'].apply(lambda x: tweet_to_root.get(x))
    
    # Final output
    output_cols = [
        'tweet_id', 'conversation_id', 'author_id', 'created_at', 
        'text', 'text_clean', 'in_response_to_tweet_id', 'previous_context'
    ]
    final_df = english_df[output_cols]
    
    os.makedirs('data/processed', exist_ok=True)
    out_path = 'data/processed/amazon_english_inbound.csv'
    final_df.to_csv(out_path, index=False)
    print(f"\nSaved clean English dataset to: {out_path}")

if __name__ == "__main__":
    prepare_data()
