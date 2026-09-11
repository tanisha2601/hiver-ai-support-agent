import os
import pandas as pd

def run_failure_analysis():
    preds_path = 'results/end_to_end_predictions.csv'
    if not os.path.exists(preds_path):
        print("Predictions not found. Run evaluate_agent.py first.")
        return
        
    df = pd.read_csv(preds_path)
    total = len(df)
    
    failures = []
    
    # 1. Intent Misclassification
    wrong_intent = df[df['predicted_intent'] != df['true_intent']]
    if len(wrong_intent) > 0:
        failures.append({
            'Failure name': 'Intent Misclassification',
            'Number of affected examples': len(wrong_intent),
            'Example': f"Tweet {wrong_intent.iloc[0]['tweet_id']}: Predicted {wrong_intent.iloc[0]['predicted_intent']}, True {wrong_intent.iloc[0]['true_intent']}",
            'Why the system failed': 'The weak-supervision trained model failed to predict the manually assigned gold intent, often due to overlapping vocabulary (e.g. delivery vs damaged).',
            'Proposed improvement': 'Gather a manually annotated training set or utilize a more powerful semantic embedding classifier.'
        })
        
    # 2. Weak Lexical/Semantic Retrieval
    weak_retrieval = df[df['grounding_status'] == 'NONE']
    if len(weak_retrieval) > 0:
        failures.append({
            'Failure name': 'Weak Retrieval (No Grounding)',
            'Number of affected examples': len(weak_retrieval),
            'Example': f"Tweet {weak_retrieval.iloc[0]['tweet_id']}",
            'Why the system failed': 'The hybrid retriever could not find any historically similar examples above the minimum similarity threshold.',
            'Proposed improvement': 'Increase the size of the historical corpus or lower the fallback retrieval threshold for safe intents.'
        })
        
    # 3. Unclear Context Handling (Over-Escalation)
    unclear = df[(df['needs_context'] == True) & (df['escalation_decision'] == 'ESCALATE') & (df['true_intent'] == df['predicted_intent'])]
    if len(unclear) > 0:
        failures.append({
            'Failure name': 'Over-escalation on Ambiguous Follow-ups',
            'Number of affected examples': len(unclear),
            'Example': f"Tweet {unclear.iloc[0]['tweet_id']}",
            'Why the system failed': 'Short messages were correctly classified but escalated aggressively due to a missing context signal.',
            'Proposed improvement': 'Build an entity extractor to check if order IDs/tracking numbers exist before escalating.'
        })
        
    # 4. Over-Escalation of Complaints
    complaints = df[(df['predicted_intent'] == 'CUSTOMER_SERVICE_COMPLAINT') & (df['escalation_decision'] == 'ESCALATE')]
    if len(complaints) > 0:
        failures.append({
            'Failure name': 'Conservative Complaint Escalation',
            'Number of affected examples': len(complaints),
            'Example': f"Tweet {complaints.iloc[0]['tweet_id']}",
            'Why the system failed': 'The policy explicitly hard-escalates all serious complaints regardless of confidence.',
            'Proposed improvement': 'Allow the agent to generate an empathetic de-escalation reply before routing to a human.'
        })
        
    # 5. Unsupported Action
    unsupported = df[(df['predicted_intent'] == 'ORDER_MODIFICATION') & (df['escalation_decision'] == 'ESCALATE') & (df['grounding_status'] != 'STRONG')]
    if len(unsupported) > 0:
        failures.append({
            'Failure name': 'Unsupported Action Escalation',
            'Number of affected examples': len(unsupported),
            'Example': f"Tweet {unsupported.iloc[0]['tweet_id']}",
            'Why the system failed': 'The user requested an action the agent cannot perform natively without high grounding.',
            'Proposed improvement': 'Implement API tool calling capabilities to actually modify orders.'
        })
        
    fail_df = pd.DataFrame(failures)
    fail_df = fail_df.sort_values(by='Number of affected examples', ascending=False)
    
    os.makedirs('results', exist_ok=True)
    os.makedirs('docs', exist_ok=True)
    
    fail_df.to_csv('results/failure_analysis.csv', index=False)
    
    with open('docs/failure-analysis.md', 'w') as f:
        f.write("# Failure Analysis\n\n")
        f.write("The top failure modes from the end-to-end evaluation are documented below.\n\n")
        for _, row in fail_df.iterrows():
            f.write(f"## {row['Failure name']}\n")
            f.write(f"- **Number of affected examples**: {row['Number of affected examples']}\n")
            f.write(f"- **Example**: {row['Example']}\n")
            f.write(f"- **Why the system failed**: {row['Why the system failed']}\n")
            f.write(f"- **Proposed improvement**: {row['Proposed improvement']}\n\n")
            
    print("Failure analysis written to results/failure_analysis.csv and docs/failure-analysis.md")

if __name__ == "__main__":
    run_failure_analysis()
