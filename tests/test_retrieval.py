import os
import pandas as pd
import pytest

def test_retrieval_metrics():
    preds_path = 'results/retrieval_predictions.csv'
    metrics_path = 'results/retrieval_metrics.csv'
    eval_path = 'data/processed/amazon_eval.csv'
    
    assert os.path.exists(preds_path), "Predictions file not found."
    assert os.path.exists(metrics_path), "Metrics file not found."
    
    preds_df = pd.read_csv(preds_path)
    eval_df = pd.read_csv(eval_path)
    
    # 1. all 200 evaluation examples receive retrieval results
    assert preds_df['evaluation_tweet_id'].nunique() == 200, "Must contain exactly 200 evaluated tweets."
    
    # 2. retrieval returns at most K results (we used 5)
    counts = preds_df.groupby('evaluation_tweet_id').size()
    assert counts.max() <= 5, "Retrieved more than 5 results per query."
    
    # 3. similarity scores are valid
    assert (preds_df['similarity_score'] >= -0.01).all() and (preds_df['similarity_score'] <= 1.01).all(), "Similarity scores out of bounds."
    
    # 4. no retrieved conversation belongs to an evaluation conversation
    eval_convs = set(eval_df['conversation_id'].unique())
    retrieved_convs = set(preds_df['retrieved_conversation_id'].unique())
    assert len(eval_convs.intersection(retrieved_convs)) == 0, "Leakage detected: Evaluation conversation found in retrieval results."
    
    # 5. no evaluation tweet is retrieved
    eval_tweets = set(eval_df['tweet_id'].unique())
    retrieved_tweets = set(preds_df['historical_tweet_id'].unique() if 'historical_tweet_id' in preds_df.columns else [])
    assert len(eval_tweets.intersection(retrieved_tweets)) == 0, "Leakage detected: Evaluation tweet found in retrieval results."
    
    # 6. retrieved results contain genuine historical responses
    assert preds_df['retrieved_historical_response'].notna().all(), "Missing historical brand response."
    assert (preds_df['retrieved_historical_response'] != '').all(), "Empty historical brand response."
    
    # 7. top scores are sorted descending
    # Group by evaluation tweet and check if sorted
    for _, group in preds_df.groupby('evaluation_tweet_id'):
        scores = group['similarity_score'].tolist()
        assert scores == sorted(scores, reverse=True), "Scores are not sorted in descending order."
        
    # 8. required output columns exist
    required_cols = [
        'evaluation_tweet_id', 'evaluation_conversation_id', 'customer_text', 
        'gold_intent', 'retrieved_rank', 'similarity_score', 
        'retrieved_customer_text', 'retrieved_historical_response', 'retrieved_conversation_id'
    ]
    for col in required_cols:
        assert col in preds_df.columns, f"Missing required column in predictions: {col}"
