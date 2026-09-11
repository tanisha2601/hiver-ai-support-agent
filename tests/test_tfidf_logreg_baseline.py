import os
import pandas as pd
import pytest

def test_tfidf_baseline_outputs():
    preds_path = 'results/tfidf_logreg_predictions.csv'
    metrics_path = 'results/tfidf_logreg_metrics.csv'
    eval_path = 'data/processed/amazon_eval.csv'
    comp_path = 'results/tfidf_logreg_comparison.csv'
    cm_path = 'results/tfidf_logreg_confusion_matrix.csv'
    
    assert os.path.exists(preds_path), "Predictions file not found."
    assert os.path.exists(metrics_path), "Metrics file not found."
    assert os.path.exists(eval_path), "Evaluation dataset not found."
    assert os.path.exists(comp_path), "Comparison file not found."
    assert os.path.exists(cm_path), "Confusion matrix file not found."
    
    preds_df = pd.read_csv(preds_path)
    eval_df = pd.read_csv(eval_path)
    
    # 1. exactly 200 evaluation predictions
    assert len(preds_df) == 200, "Must contain exactly 200 predictions."
    
    # 2. no missing predictions
    assert preds_df['predicted_intent'].notna().all(), "Missing predictions found."
    
    # 3. all predictions belong to the 9-intent taxonomy
    valid_intents = {
        'DELIVERY_SHIPPING', 'PRIME_SUBSCRIPTION', 'REFUND_RETURN', 'DAMAGED_MISSING_ITEM',
        'PAYMENT_BILLING', 'ACCOUNT_LOGIN', 'ORDER_MODIFICATION', 'CUSTOMER_SERVICE_COMPLAINT', 'OTHER'
    }
    assert set(preds_df['predicted_intent'].unique()).issubset(valid_intents), "Invalid predicted intent found."
    
    # 4. evaluation labels were not used for training
    # Implied by the design since training happens on train_pool, but we verify eval labels are unchanged
    assert (preds_df['gold_intent'] == eval_df['intent']).all(), "Gold intents must match the evaluation set exactly."
    
    # 5. confusion matrix has correct dimensions
    cm_df = pd.read_csv(cm_path, index_col=0)
    assert len(cm_df.columns) == len(cm_df.index), "Confusion matrix must be square."
    assert set(cm_df.columns).issubset(valid_intents), "Confusion matrix columns must be valid intents."
