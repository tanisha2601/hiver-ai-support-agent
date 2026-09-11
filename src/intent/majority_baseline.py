import os
import pandas as pd
import numpy as np
import re
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report

def estimate_majority_intent(train_path):
    """
    Since the train pool is technically unlabeled in this project phase,
    we use a fast heuristic to estimate the majority intent class 
    across the entire training pool.
    """
    print("Estimating majority intent from training pool...")
    df = pd.read_csv(train_path)
    
    # Fast vectorized keyword matching for the top intents
    # Based on exploratory analysis, DELIVERY_SHIPPING is the most frequent.
    # We will verify this by counting.
    
    delivery_mask = df['text_clean'].str.contains(r'(?i)\b(delivery|shipping|shipped|arrive|arrived|package|tracking|track|late|delayed)\b', na=False)
    prime_mask = df['text_clean'].str.contains(r'(?i)\b(prime|subscription|membership|renew)\b', na=False)
    refund_mask = df['text_clean'].str.contains(r'(?i)\b(refund|return|returned|money back)\b', na=False)
    
    counts = {
        'DELIVERY_SHIPPING': delivery_mask.sum(),
        'PRIME_SUBSCRIPTION': prime_mask.sum(),
        'REFUND_RETURN': refund_mask.sum()
    }
    
    majority_intent = max(counts, key=counts.get)
    majority_count = counts[majority_intent]
    
    print(f"Estimated Majority Intent: {majority_intent} (approx. {majority_count} examples)")
    return majority_intent, majority_count

def run_baseline():
    train_path = 'data/processed/amazon_train_pool.csv'
    eval_path = 'data/processed/amazon_eval.csv'
    
    if not os.path.exists(train_path) or not os.path.exists(eval_path):
        print("Required datasets not found.")
        return
        
    majority_intent, train_count = estimate_majority_intent(train_path)
    
    print(f"Evaluating majority baseline on {eval_path}...")
    eval_df = pd.read_csv(eval_path)
    
    # Predict the majority intent for every evaluation example
    eval_df['predicted_intent'] = majority_intent
    
    y_true = eval_df['intent']
    y_pred = eval_df['predicted_intent']
    
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, average='macro', zero_division=0)
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted', zero_division=0)
    
    # Save predictions
    preds_df = eval_df[['tweet_id', 'conversation_id', 'customer_text', 'intent', 'predicted_intent']].copy()
    preds_df.rename(columns={'intent': 'gold_intent'}, inplace=True)
    os.makedirs('results', exist_ok=True)
    preds_df.to_csv('results/majority_baseline_predictions.csv', index=False)
    
    # Save metrics
    metrics_df = pd.DataFrame([{
        'majority_intent': majority_intent,
        'train_examples_estimated': train_count,
        'accuracy': accuracy,
        'macro_precision': precision_macro,
        'macro_recall': recall_macro,
        'macro_f1': f1_macro,
        'weighted_f1': f1_weighted
    }])
    metrics_df.to_csv('results/majority_baseline_metrics.csv', index=False)
    
    # Classification report
    report_dict = classification_report(y_true, y_pred, zero_division=0, output_dict=True)
    report_df = pd.DataFrame(report_dict).transpose()
    report_df.to_csv('results/majority_baseline_classification_report.csv', index=True)
    
    # Confusion matrix
    labels = sorted(y_true.unique())
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    cm_df.to_csv('results/majority_baseline_confusion_matrix.csv', index=True)
    
    print("\n--- RESULTS ---")
    print(f"Majority Intent: {majority_intent}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {f1_macro:.4f}")
    print(f"Weighted F1: {f1_weighted:.4f}")

if __name__ == "__main__":
    run_baseline()
