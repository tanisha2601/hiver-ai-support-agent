"""
Golden Candidate Sampling Script

This script generates a candidate pool of ~200 diverse, unannotated examples 
from the cleaned AmazonHelp dataset to serve as the golden evaluation set.

It uses keyword-based heuristics to ensure a stratified sample of likely 
intents (Delivery, Prime, Refunds, Damaged, Complaints, Follow-ups), 
but DOES NOT automatically assign the final intent labels.
"""

import os
import pandas as pd
import numpy as np

def create_candidates():
    input_path = 'data/processed/amazon_english_inbound.csv'
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    print(f"Loading cleaned dataset from {input_path}...")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} records.")

    # We will stratify by heuristic buckets to ensure diversity.
    # Note: These buckets are ONLY for sampling diversity, not for labeling.
    
    # 1. Delivery / Shipping (Target: ~30)
    delivery_mask = df['text_clean'].str.contains(r'(?i)\b(delivery|shipping|shipped|arrive|arrived|package|tracking|track)\b')
    
    # 2. Prime / Subscription (Target: ~30)
    prime_mask = df['text_clean'].str.contains(r'(?i)\b(prime|subscription|membership|renew)\b')
    
    # 3. Refunds / Returns (Target: ~30)
    refund_mask = df['text_clean'].str.contains(r'(?i)\b(refund|return|returned|money back|charge)\b')
    
    # 4. Damaged / Missing (Target: ~20)
    damaged_mask = df['text_clean'].str.contains(r'(?i)\b(damaged|missing|broken|empty|stolen)\b')
    
    # 5. Customer Service / Complaints (Target: ~30)
    complaint_mask = df['text_clean'].str.contains(r'(?i)\b(customer service|support|chat|call|rude|hold|terrible|worst)\b')
    
    # 6. Context-Dependent / Follow-ups (Short text, length < 30) (Target: ~20)
    short_mask = (df['text_clean'].str.len() < 30) & df['previous_context'].notna()

    # Create disjoint buckets to sample from
    df['bucket'] = 'Random/Other'
    
    # Assign buckets (order matters for disjoint sets)
    df.loc[short_mask, 'bucket'] = 'FollowUp'
    df.loc[complaint_mask & (df['bucket'] == 'Random/Other'), 'bucket'] = 'Complaint'
    df.loc[damaged_mask & (df['bucket'] == 'Random/Other'), 'bucket'] = 'Damaged'
    df.loc[refund_mask & (df['bucket'] == 'Random/Other'), 'bucket'] = 'Refund'
    df.loc[prime_mask & (df['bucket'] == 'Random/Other'), 'bucket'] = 'Prime'
    df.loc[delivery_mask & (df['bucket'] == 'Random/Other'), 'bucket'] = 'Delivery'

    # Sampling strategy (Target: 200)
    targets = {
        'Delivery': 35,
        'Prime': 35,
        'Refund': 35,
        'Damaged': 25,
        'Complaint': 30,
        'FollowUp': 20,
        'Random/Other': 20
    }

    sampled_dfs = []
    np.random.seed(42) # For reproducibility

    for bucket, target in targets.items():
        bucket_df = df[df['bucket'] == bucket]
        if len(bucket_df) >= target:
            sampled = bucket_df.sample(n=target, random_state=42)
        else:
            sampled = bucket_df
        sampled_dfs.append(sampled)

    candidates_df = pd.concat(sampled_dfs).sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"\nSampled {len(candidates_df)} golden candidates.")
    print("Distribution of heuristic buckets (for sampling diversity only):")
    print(candidates_df['bucket'].value_counts())

    # Format for manual annotation
    annotation_df = pd.DataFrame({
        'example_id': [f"GOLD_{i:03d}" for i in range(1, len(candidates_df) + 1)],
        'tweet_id': candidates_df['tweet_id'],
        'conversation_id': candidates_df['conversation_id'],
        'customer_text': candidates_df['text_clean'],
        'previous_context': candidates_df['previous_context'],
        'intent': '',            # BLANK FOR MANUAL ANNOTATION
        'difficulty': '',        # BLANK FOR MANUAL ANNOTATION
        'needs_context': '',     # BLANK FOR MANUAL ANNOTATION
        'annotation_notes': ''   # BLANK FOR MANUAL ANNOTATION
    })

    os.makedirs('evaluation', exist_ok=True)
    out_path = 'evaluation/golden_set.csv'
    annotation_df.to_csv(out_path, index=False)
    print(f"\nSaved golden candidate set to: {out_path}")
    print("NOTE: The 'intent', 'difficulty', and 'needs_context' fields are left completely blank.")
    print("They MUST be manually annotated before proceeding.")

if __name__ == "__main__":
    create_candidates()
