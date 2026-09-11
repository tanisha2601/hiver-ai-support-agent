import pandas as pd
import os
import pytest

def test_evaluation_split_integrity():
    eval_path = 'data/processed/amazon_eval.csv'
    train_path = 'data/processed/amazon_train_pool.csv'
    
    assert os.path.exists(eval_path), "Evaluation dataset not found."
    assert os.path.exists(train_path), "Training pool not found."
    
    eval_df = pd.read_csv(eval_path)
    train_df = pd.read_csv(train_path)
    
    # 1. exactly 200 examples
    assert len(eval_df) == 200, "Evaluation set must contain exactly 200 examples"
    
    # 2. all 200 tweet_ids unique
    assert eval_df['tweet_id'].nunique() == 200, "All tweet_ids in eval set must be unique"
    
    # 3. all 200 conversation_ids valid
    assert eval_df['conversation_id'].notna().all(), "All eval conversation_ids must be valid (not na)"
    
    # 4. no eval conversation_id exists in training pool
    eval_convs = set(eval_df['conversation_id'].unique())
    train_convs = set(train_df['conversation_id'].unique())
    assert len(eval_convs.intersection(train_convs)) == 0, "Leakage detected: Evaluation conversation found in training pool"
    
    # 5. no eval tweet_id exists in training pool
    eval_tweets = set(eval_df['tweet_id'].unique())
    train_tweets = set(train_df['tweet_id'].unique())
    assert len(eval_tweets.intersection(train_tweets)) == 0, "Leakage detected: Evaluation tweet found in training pool"
    
    # 6. required columns exist
    required_eval_cols = [
        'tweet_id', 'conversation_id', 'customer_text', 
        'previous_context', 'intent', 'difficulty', 'needs_context'
    ]
    for col in required_eval_cols:
        assert col in eval_df.columns, f"Missing required column in eval set: {col}"
        
    # 7. no blank labels
    assert eval_df['intent'].notna().all(), "Intent cannot have blank values"
    assert eval_df['difficulty'].notna().all(), "Difficulty cannot have blank values"
    assert eval_df['needs_context'].notna().all(), "needs_context cannot have blank values"
    
    # 8. intent values valid
    valid_intents = {
        'DELIVERY_SHIPPING', 'PRIME_SUBSCRIPTION', 'REFUND_RETURN', 'DAMAGED_MISSING_ITEM',
        'PAYMENT_BILLING', 'ACCOUNT_LOGIN', 'ORDER_MODIFICATION', 'CUSTOMER_SERVICE_COMPLAINT', 'OTHER'
    }
    assert set(eval_df['intent'].unique()).issubset(valid_intents), "Invalid intent value found"
    
    # 9. difficulty values valid
    assert set(eval_df['difficulty'].unique()).issubset({'easy', 'medium', 'hard'}), "Invalid difficulty value found"
    
    # 10. needs_context values valid
    assert set(eval_df['needs_context'].unique()).issubset({True, False}), "Invalid needs_context value found"
