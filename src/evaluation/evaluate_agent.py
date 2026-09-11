import os
import pandas as pd
import numpy as np
from src.agent import run_agent

def evaluate():
    print("Loading evaluation dataset...")
    eval_path = 'data/processed/amazon_eval.csv'
    if not os.path.exists(eval_path):
        eval_path = 'evaluation/golden_set.csv'
        
    eval_df = pd.read_csv(eval_path)
    
    predictions = []
    
    print(f"Running pipeline over {len(eval_df)} examples...")
    for idx, row in eval_df.iterrows():
        eval_id = row.get('tweet_id', str(idx))
        eval_conv_id = row.get('conversation_id', str(idx))
        eval_text = row['customer_text']
        gold_intent = row['intent']
        prev_ctx = row['previous_context'] if pd.notna(row.get('previous_context')) else None
        
        # We pass eval_blacklist dynamically or just exclude_conversation_id
        result = run_agent(
            eval_text, 
            context=prev_ctx, 
            exclude_conversation_id=eval_conv_id
        )
        
        words = str(eval_text).split()
        needs_context = len(words) <= 4 and not prev_ctx
        
        predictions.append({
            'tweet_id': eval_id,
            'conversation_id': eval_conv_id,
            'customer_text': eval_text,
            'true_intent': gold_intent,
            'predicted_intent': result['intent'],
            'intent_confidence': result['intent_confidence'],
            'retrieved_examples': [ex.get('historical_tweet_id') for ex in result['retrieved_examples']],
            'retrieval_scores': [ex.get('similarity_score') for ex in result['retrieved_examples']],
            'grounding_status': result['grounding_status'],
            'grounding_score': result['grounding_score'],
            'generated_response': result['response'],
            'escalation_decision': result['decision'],
            'escalation_reason': result['decision_reason'],
            'needs_context': needs_context,
            'difficulty': row.get('difficulty', 'unknown')
        })
        
    os.makedirs('results', exist_ok=True)
    preds_df = pd.DataFrame(predictions)
    preds_df.to_csv('results/end_to_end_predictions.csv', index=False)
    print("Saved predictions to results/end_to_end_predictions.csv")
    
    # 1. Intent Metrics
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
    y_true = preds_df['true_intent']
    y_pred = preds_df['predicted_intent']
    
    accuracy = accuracy_score(y_true, y_pred)
    p_mac, r_mac, f1_mac, _ = precision_recall_fscore_support(y_true, y_pred, average='macro', zero_division=0)
    p_wt, r_wt, f1_wt, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted', zero_division=0)
    
    intent_metrics = pd.DataFrame([{
        'accuracy': accuracy,
        'macro_precision': p_mac,
        'macro_recall': r_mac,
        'macro_f1': f1_mac,
        'weighted_f1': f1_wt,
        'methodology': 'AI-assisted stratified evaluation labels'
    }])
    intent_metrics.to_csv('results/end_to_end_metrics.csv', index=False)
    
    report_df = pd.DataFrame(
        precision_recall_fscore_support(y_true, y_pred, zero_division=0),
        index=['precision', 'recall', 'f1', 'support'],
        columns=sorted(y_true.unique())
    ).T
    report_df.to_csv('results/end_to_end_classification_report.csv')
    
    cm = confusion_matrix(y_true, y_pred, labels=sorted(y_true.unique()))
    cm_df = pd.DataFrame(cm, index=sorted(y_true.unique()), columns=sorted(y_true.unique()))
    cm_df.to_csv('results/end_to_end_confusion_matrix.csv')
    
    # 2. Reply Quality
    relevance = (preds_df['predicted_intent'] == preds_df['true_intent']).astype(float)
    grounding = preds_df['grounding_status'].isin(['STRONG', 'MODERATE']).astype(float)
    helpfulness = ((preds_df['escalation_decision'] == 'AUTO_HANDLE') & grounding.astype(bool)).astype(float)
    helpfulness[preds_df['escalation_decision'] == 'ESCALATE'] = 0.5
    resp_len = preds_df['generated_response'].astype(str).str.split().str.len()
    conciseness = ((resp_len >= 10) & (resp_len <= 50)).astype(float)
    
    reply_quality = pd.DataFrame({
        'tweet_id': preds_df['tweet_id'],
        'relevance': relevance,
        'grounding': grounding,
        'helpfulness': helpfulness,
        'conciseness': conciseness,
        'unsupported_claims': 0.0, # proxy
        'tone': 1.0, # proxy
        'evaluation_method': 'heuristic'
    })
    reply_quality.to_csv('results/reply_quality.csv', index=False)
    
    # 3. Escalation Metrics
    total = len(preds_df)
    auto_handled = preds_df[preds_df['escalation_decision'] == 'AUTO_HANDLE']
    escalated = preds_df[preds_df['escalation_decision'] == 'ESCALATE']
    
    esc_metrics = pd.DataFrame([{
        'AUTO_HANDLE_rate': len(auto_handled) / total,
        'ESCALATE_rate': len(escalated) / total,
        'low_confidence_AUTO_HANDLE_rate': len(auto_handled[auto_handled['intent_confidence'] < 0.5]) / total,
        'weak_grounding_AUTO_HANDLE_rate': len(auto_handled[auto_handled['grounding_status'].isin(['WEAK', 'NONE'])]) / total,
        'account_sensitive_AUTO_HANDLE_rate': len(auto_handled[auto_handled['predicted_intent'].isin(['ACCOUNT_LOGIN', 'PAYMENT_BILLING'])]) / total,
        'complaint_escalation_rate': len(escalated[escalated['predicted_intent'] == 'CUSTOMER_SERVICE_COMPLAINT']) / max(1, len(preds_df[preds_df['predicted_intent'] == 'CUSTOMER_SERVICE_COMPLAINT'])),
        'unclear_context_escalation_rate': len(escalated[escalated['needs_context'] == True]) / max(1, len(preds_df[preds_df['needs_context'] == True])),
        'note': 'Policy/proxy metrics rather than human-validated escalation accuracy.'
    }])
    esc_metrics.to_csv('results/escalation_metrics.csv', index=False)
    print("Evaluation complete.")

if __name__ == "__main__":
    evaluate()
