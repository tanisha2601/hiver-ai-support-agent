"""
Exploratory Intent and Customer Query Analysis across Candidate Brands.
Identifies customer problem themes, n-grams, and representative examples.
"""

import sys
import os
import re
import random
from collections import Counter
import pandas as pd
import numpy as np

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def find_dataset(raw_dir: str = "data/raw") -> str:
    import glob
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    return csv_files[0] if csv_files else "data/raw/twcs.csv"

def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r'@[A-Za-z0-9_]+', '', text)  # remove user/brand handles
    text = re.sub(r'https?://\S+', '', text)    # remove URLs
    text = re.sub(r'\s+', ' ', text)           # normalize whitespace
    return text.strip()

def run_intent_exploration():
    dataset_path = find_dataset()
    print(f"Loading data from {dataset_path}...")
    df = pd.read_csv(
        dataset_path,
        usecols=['tweet_id', 'author_id', 'inbound', 'text', 'in_response_to_tweet_id'],
        low_memory=False
    )

    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'to', 'for', 'is', 'in', 'on', 'my', 'i', 'it', 'this',
        'me', 'you', 'with', 'of', 'have', 'be', 'at', 'so', 'just', 'can', 'not', 'that', 'but',
        'how', 'do', 'what', 'when', 'why', 'are', 'was', 'im', 'all', 'as', 'any', 'get', 'if',
        'we', 'from', 'they', 'like', 'there', 'out', 'up', 'been', 'about', 'has', 'now', 'will',
        'by', 'after', 'your', 'its', 'even', 'still', 'into', 'would', 'could', 'should', 'more',
        'over', 'am', 'no', 'one', 'got', 'some', 'than', 'them', 'who', 'which', 'did', 'does',
        'cant', 'dont', 'wont', 'ive', 'id', 'ur', 'u', 'r', 'via', 'dm', 'please', 'help', 'hi',
        'hey', 'hello', 'thanks', 'thank'
    }

    target_brands = ['AppleSupport', 'AmazonHelp', 'SpotifyCares', 'Uber_Support', 'Delta']

    for brand in target_brands:
        print("=" * 80)
        print(f"BRAND INTENT & THEME EXPLORATION: {brand}")
        print("=" * 80)

        brand_tweets = df[df['author_id'] == brand]
        parents = set(brand_tweets['in_response_to_tweet_id'].dropna().astype(int))
        cust_df = df[df['tweet_id'].isin(parents)]

        raw_texts = cust_df['text'].dropna().tolist()
        cleaned_texts = [clean_text(t) for t in raw_texts if len(clean_text(t)) > 10]

        print(f"Customer Inquiries Analyzed: {len(cleaned_texts):,}")

        unigram_counts = Counter()
        bigram_counts = Counter()

        for text in cleaned_texts:
            tokens = [w.lower() for w in re.findall(r'[a-zA-Z]{2,}', text)]
            content_tokens = [w for w in tokens if w not in stopwords]
            unigram_counts.update(content_tokens)
            for i in range(len(content_tokens) - 1):
                bigram_counts.update([(content_tokens[i], content_tokens[i+1])])

        print("\nTop 15 Keywords (Unigrams):")
        for word, count in unigram_counts.most_common(15):
            print(f"  - {word:<15}: {count:,}")

        print("\nTop 15 Problem Phrases (Bigrams):")
        for (w1, w2), count in bigram_counts.most_common(15):
            print(f"  - {w1 + ' ' + w2:<25}: {count:,}")

        # Representative thematic query samples
        random.seed(42)
        sample_queries = [s for s in cleaned_texts if 30 < len(s) < 160]
        print(f"\nRepresentative Customer Queries (Sample of 10):")
        for i, sample in enumerate(random.sample(sample_queries, min(10, len(sample_queries))), 1):
            print(f"  {i}. {sample}")
        print("\n")

if __name__ == "__main__":
    run_intent_exploration()
