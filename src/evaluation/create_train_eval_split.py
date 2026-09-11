import os
import pandas as pd

def create_splits():
    # Load golden set
    golden_path = 'evaluation/golden_set.csv'
    if not os.path.exists(golden_path):
        print(f"Error: {golden_path} not found.")
        return
        
    golden_df = pd.read_csv(golden_path)
    golden_conv_ids = set(golden_df['conversation_id'].unique())
    
    # Load full pool
    pool_path = 'data/processed/amazon_english_inbound.csv'
    if not os.path.exists(pool_path):
        print(f"Error: {pool_path} not found.")
        return
        
    pool_df = pd.read_csv(pool_path)
    initial_messages = len(pool_df)
    
    # Exclude golden conversations
    train_pool_df = pool_df[~pool_df['conversation_id'].isin(golden_conv_ids)].copy()
    final_messages = len(train_pool_df)
    
    excluded_messages = initial_messages - final_messages
    
    # Check what was actually excluded
    excluded_df = pool_df[pool_df['conversation_id'].isin(golden_conv_ids)]
    excluded_convs = len(excluded_df['conversation_id'].unique())
    
    # Leakage check
    train_conv_ids = set(train_pool_df['conversation_id'].unique())
    leakage_intersection = golden_conv_ids.intersection(train_conv_ids)
    leakage_status = "PASS" if len(leakage_intersection) == 0 else f"FAIL ({len(leakage_intersection)} overlaps)"
    
    # Output evaluation set
    eval_cols = [
        'tweet_id', 'conversation_id', 'customer_text', 
        'previous_context', 'intent', 'difficulty', 'needs_context'
    ]
    eval_df = golden_df[eval_cols]
    eval_df.to_csv('data/processed/amazon_eval.csv', index=False)
    
    # Output training pool
    train_cols = [
        'tweet_id', 'conversation_id', 'author_id', 'created_at',
        'text', 'text_clean', 'in_response_to_tweet_id', 'previous_context'
    ]
    # some columns like text_clean might just be in the pool
    train_out_cols = [col for col in train_cols if col in train_pool_df.columns]
    train_pool_df[train_out_cols].to_csv('data/processed/amazon_train_pool.csv', index=False)
    
    # Output metrics
    metrics = {
        'total_golden_examples': len(golden_df),
        'unique_golden_conversations': len(golden_conv_ids),
        'total_amazon_messages_before_exclusion': initial_messages,
        'total_messages_after_exclusion': final_messages,
        'excluded_messages': excluded_messages,
        'excluded_conversations': excluded_convs,
        'leakage_check': leakage_status
    }
    
    metrics_df = pd.DataFrame([metrics])
    os.makedirs('results', exist_ok=True)
    metrics_df.to_csv('results/evaluation_split_metrics.csv', index=False)
    
    print("Split completed.")
    for k, v in metrics.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    create_splits()
