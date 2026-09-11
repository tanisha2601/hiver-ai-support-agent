import os
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
import warnings

warnings.filterwarnings('ignore')

def weak_label(text, prev):
    """
    Weak supervision heuristic based on intent taxonomy.
    """
    text = str(text).lower()
    prev = str(prev).lower()
    has_prev = pd.notna(prev) and prev != 'nan' and prev != ''
    
    needs_context = False
    if len(text.split()) <= 4 or re.search(r'^(yes|no|done|ok|okay|still waiting|i did|already did|thanks|ty|thank you|that didn\'t work|it didn\'t work)', text):
        needs_context = True
        
    full_text = text
    if needs_context and has_prev:
        full_text = text + " " + prev
        
    if re.search(r'\b(damaged|missing|broken|empty|stolen|cracked|wrong item|defective|shattered|ruined)\b', full_text):
        return 'DAMAGED_MISSING_ITEM'
    elif re.search(r'\b(password|locked|hacked|otp|access|login|log in|email address|can\'t log|cannot access)\b', full_text) and 'prime' not in full_text:
        return 'ACCOUNT_LOGIN'
    elif re.search(r'\b(card|charged twice|double charge|declined|gift card|payment method|balance|unauthorized charge|bank|charged me)\b', full_text):
        if 'prime' in full_text:
            return 'PRIME_SUBSCRIPTION'
        else:
            return 'PAYMENT_BILLING'
    elif re.search(r'\b(cancel order|cancel my order|change my address|update address|wrong address|change color|change size|wrong size|modify order|cancel this order)\b', full_text):
        return 'ORDER_MODIFICATION'
    elif re.search(r'\b(refund|return|returned|money back|returning)\b', full_text):
        if 'prime' in full_text and 'membership' in full_text:
            return 'PRIME_SUBSCRIPTION'
        else:
            return 'REFUND_RETURN'
    elif re.search(r'\b(delivery|shipping|shipped|arrive|arrived|package|tracking|track|late|delayed|where is my)\b', full_text):
        return 'DELIVERY_SHIPPING'
    elif re.search(r'\b(prime|subscription|membership|renew|subscribe)\b', full_text):
        return 'PRIME_SUBSCRIPTION'
    elif re.search(r'\b(customer service|support|chat|call|rude|hold|terrible|worst|useless|transfer|on hold)\b', text):
        return 'CUSTOMER_SERVICE_COMPLAINT'
    else:
        return 'OTHER'

def train_and_evaluate(X_train, y_train, X_test, y_test, variant_name):
    print(f"\nTraining Model: {variant_name}")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, min_df=3, stop_words='english')
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    clf = LogisticRegression(class_weight='balanced', max_iter=500, random_state=42)
    clf.fit(X_train_vec, y_train)
    
    y_pred = clf.predict(X_test_vec)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)
    
    print(f"[{variant_name}] Accuracy: {accuracy:.4f} | Macro F1: {f1_macro:.4f} | Weighted F1: {f1_weighted:.4f}")
    
    return {
        'input_variant': variant_name,
        'accuracy': accuracy,
        'macro_precision': precision_macro,
        'macro_recall': recall_macro,
        'macro_f1': f1_macro,
        'weighted_f1': f1_weighted
    }, y_pred

def run_logreg_baseline():
    train_path = 'data/processed/amazon_train_pool.csv'
    eval_path = 'data/processed/amazon_eval.csv'
    
    if not os.path.exists(train_path) or not os.path.exists(eval_path):
        print("Required datasets not found.")
        return
        
    print("Loading training data and creating weak labels...")
    train_df = pd.read_csv(train_path)
    
    # Subsample to speed up weak labeling and training since 178k is huge for simple heuristics
    # We take 20,000 examples to make it computationally trivial while retaining plenty of data
    train_df = train_df.sample(n=20000, random_state=42).reset_index(drop=True)
    
    train_df['weak_intent'] = train_df.apply(lambda row: weak_label(row['text_clean'], row['previous_context']), axis=1)
    print(f"Weak labels distribution over {len(train_df)} examples:")
    print(train_df['weak_intent'].value_counts())
    
    print("Loading evaluation data...")
    eval_df = pd.read_csv(eval_path)
    y_test = eval_df['intent']
    
    # Text-only input
    train_df['input_text_only'] = train_df['text_clean'].fillna('')
    eval_df['input_text_only'] = eval_df['customer_text'].fillna('')
    
    # Text + Context input
    train_df['input_with_context'] = train_df['text_clean'].fillna('') + " " + train_df['previous_context'].fillna('')
    eval_df['input_with_context'] = eval_df['customer_text'].fillna('') + " " + eval_df['previous_context'].fillna('')
    
    # Evaluate Variant A (Text Only)
    res_a, y_pred_a = train_and_evaluate(
        train_df['input_text_only'], train_df['weak_intent'], 
        eval_df['input_text_only'], y_test, 
        'customer_text_only'
    )
    
    # Evaluate Variant B (Text + Context)
    res_b, y_pred_b = train_and_evaluate(
        train_df['input_with_context'], train_df['weak_intent'], 
        eval_df['input_with_context'], y_test, 
        'customer_text_and_context'
    )
    
    # Save the BEST model's full results. Let's say Context model is expected to be better or we just pick B as default.
    # We will save variant B's predictions and reports as the main output, but compare both in the comparison CSV.
    os.makedirs('results', exist_ok=True)
    
    # Predictions
    preds_df = eval_df[['tweet_id', 'conversation_id', 'customer_text', 'previous_context', 'intent']].copy()
    preds_df.rename(columns={'intent': 'gold_intent'}, inplace=True)
    preds_df['predicted_intent'] = y_pred_b  # Using variant B for the main predictions CSV
    preds_df.to_csv('results/tfidf_logreg_predictions.csv', index=False)
    
    # Comparison
    comp_df = pd.DataFrame([res_a, res_b])
    comp_df.to_csv('results/tfidf_logreg_comparison.csv', index=False)
    
    # Main metrics
    metrics_df = pd.DataFrame([res_b])
    metrics_df.to_csv('results/tfidf_logreg_metrics.csv', index=False)
    
    # Classification report
    report_dict = classification_report(y_test, y_pred_b, zero_division=0, output_dict=True)
    report_df = pd.DataFrame(report_dict).transpose()
    report_df.to_csv('results/tfidf_logreg_classification_report.csv', index=True)
    
    # Confusion matrix
    labels = sorted(y_test.unique())
    cm = confusion_matrix(y_test, y_pred_b, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    cm_df.to_csv('results/tfidf_logreg_confusion_matrix.csv', index=True)
    
    print("\nProcessing complete. All results saved to 'results/' directory.")

if __name__ == "__main__":
    run_logreg_baseline()
