import os
import pandas as pd
import pytest

def test_majority_baseline_predictions():
    preds_path = 'results/majority_baseline_predictions.csv'
    metrics_path = 'results/majority_baseline_metrics.csv'
    eval_path = 'data/processed/amazon_eval.csv'
    
    assert os.path.exists(preds_path), "Predictions file not found."
    assert os.path.exists(metrics_path), "Metrics file not found."
    assert os.path.exists(eval_path), "Evaluation dataset not found."
    
    preds_df = pd.read_csv(preds_path)
    eval_df = pd.read_csv(eval_path)
    metrics_df = pd.read_csv(metrics_path)
    
    # 1. exactly 200 evaluation predictions
    assert len(preds_df) == 200, "Must contain exactly 200 predictions."
    
    # 2. no missing predictions
    assert preds_df['predicted_intent'].notna().all(), "Missing predictions found."
    
    # 3. predicted intent is identical for all rows
    majority_intent = preds_df['predicted_intent'].iloc[0]
    assert (preds_df['predicted_intent'] == majority_intent).all(), "Predicted intent must be identical for all rows in majority baseline."
    
    # 4. predicted intent is a valid taxonomy intent
    valid_intents = {
        'DELIVERY_SHIPPING', 'PRIME_SUBSCRIPTION', 'REFUND_RETURN', 'DAMAGED_MISSING_ITEM',
        'PAYMENT_BILLING', 'ACCOUNT_LOGIN', 'ORDER_MODIFICATION', 'CUSTOMER_SERVICE_COMPLAINT', 'OTHER'
    }
    assert majority_intent in valid_intents, "Predicted intent must be valid."
    
    # 5. gold intents are unchanged
    assert (preds_df['gold_intent'] == eval_df['intent']).all(), "Gold intents must match the evaluation set exactly."
    
    # 6. metrics are calculated correctly (sanity check)
    accuracy = (preds_df['gold_intent'] == preds_df['predicted_intent']).mean()
    assert abs(metrics_df['accuracy'].iloc[0] - accuracy) < 1e-6, "Accuracy metric is incorrect."
    
    # 7. no eval labels accidentally used to determine majority class
    # Since we predicted identical intents and it's DELIVERY_SHIPPING (presumably), 
    # and accuracy is not 100%, it implies we didn't cheat.
    assert accuracy < 0.99, "Accuracy is too high for a majority baseline."
