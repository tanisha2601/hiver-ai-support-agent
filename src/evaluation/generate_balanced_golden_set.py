import os
import pandas as pd
import numpy as np
import re

def generate_balanced_set():
    input_path = 'data/processed/amazon_english_inbound.csv'
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    print(f"Loading dataset from {input_path}...")
    df = pd.read_csv(input_path)
    # Shuffle dataset to get random genuine examples
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    targets = {
        'DELIVERY_SHIPPING': 25,
        'PRIME_SUBSCRIPTION': 20,
        'REFUND_RETURN': 25,
        'DAMAGED_MISSING_ITEM': 20,
        'PAYMENT_BILLING': 15,
        'ACCOUNT_LOGIN': 15,
        'ORDER_MODIFICATION': 15,
        'CUSTOMER_SERVICE_COMPLAINT': 25,
        'OTHER': 40
    }

    collected = {k: [] for k in targets}
    
    def determine_intent(text, prev):
        text = str(text).lower()
        prev = str(prev).lower()
        has_prev = pd.notna(prev) and prev != 'nan' and prev != ''
        
        needs_context = False
        difficulty = 'hard'
        confidence = 'low'
        reason = 'Fallback'
        
        # Check if short/context-dependent
        if len(text.split()) <= 4 or re.search(r'^(yes|no|done|ok|okay|still waiting|i did|already did|thanks|ty|thank you|that didn\'t work|it didn\'t work)', text):
            needs_context = True
            difficulty = 'medium'
            
        full_text = text
        if needs_context and has_prev:
            full_text = text + " " + prev
            
        # Semantic Heuristics
        intent = None
        
        # 1. DAMAGED_MISSING_ITEM
        if re.search(r'\b(damaged|missing|broken|empty|stolen|cracked|wrong item|defective|shattered|ruined)\b', full_text):
            intent = 'DAMAGED_MISSING_ITEM'
            confidence = 'high' if re.search(r'\b(damaged|broken|empty|stolen)\b', text) else 'medium'
            difficulty = 'easy' if confidence == 'high' else 'medium'
            reason = 'Matches damage/missing keywords'
            
        # 2. ACCOUNT_LOGIN
        elif re.search(r'\b(password|locked|hacked|otp|access|login|log in|email address|can\'t log|cannot access)\b', full_text) and 'prime' not in full_text:
            intent = 'ACCOUNT_LOGIN'
            confidence = 'high' if 'locked' in text or 'password' in text else 'medium'
            difficulty = 'easy'
            reason = 'Matches account/security keywords'
            
        # 3. PAYMENT_BILLING
        elif re.search(r'\b(card|charged twice|double charge|declined|gift card|payment method|balance|unauthorized charge|bank|charged me)\b', full_text):
            if 'prime' in full_text:
                intent = 'PRIME_SUBSCRIPTION'
                confidence = 'medium'
                difficulty = 'medium'
                reason = 'Payment issue related to prime'
            else:
                intent = 'PAYMENT_BILLING'
                confidence = 'high'
                difficulty = 'easy'
                reason = 'Matches payment/billing keywords'
                
        # 4. ORDER_MODIFICATION
        elif re.search(r'\b(cancel order|cancel my order|change my address|update address|wrong address|change color|change size|wrong size|modify order|cancel this order)\b', full_text):
            intent = 'ORDER_MODIFICATION'
            confidence = 'high'
            difficulty = 'easy'
            reason = 'Matches order modification keywords'
            
        # 5. REFUND_RETURN
        elif re.search(r'\b(refund|return|returned|money back|returning)\b', full_text):
            if 'prime' in full_text and 'membership' in full_text:
                intent = 'PRIME_SUBSCRIPTION'
                reason = 'Refund requested for Prime'
                difficulty = 'medium'
                confidence = 'medium'
            else:
                intent = 'REFUND_RETURN'
                confidence = 'high'
                difficulty = 'easy'
                reason = 'Matches refund/return keywords'
                
        # 6. DELIVERY_SHIPPING
        elif re.search(r'\b(delivery|shipping|shipped|arrive|arrived|package|tracking|track|late|delayed|where is my)\b', full_text):
            intent = 'DELIVERY_SHIPPING'
            confidence = 'high'
            difficulty = 'easy'
            reason = 'Matches delivery/shipping keywords'
            
        # 7. PRIME_SUBSCRIPTION
        elif re.search(r'\b(prime|subscription|membership|renew|subscribe)\b', full_text):
            intent = 'PRIME_SUBSCRIPTION'
            confidence = 'high'
            difficulty = 'easy'
            reason = 'Matches Prime keywords'
            
        # 8. CUSTOMER_SERVICE_COMPLAINT
        elif re.search(r'\b(customer service|support|chat|call|rude|hold|terrible|worst|useless|transfer|on hold)\b', text):
            intent = 'CUSTOMER_SERVICE_COMPLAINT'
            confidence = 'medium'
            difficulty = 'medium'
            reason = 'Matches complaint/frustration keywords without specific order issue'
            
        else:
            intent = 'OTHER'
            confidence = 'low'
            difficulty = 'hard'
            reason = 'No distinct intent keywords found'
            
        # Overrides for short/contextless messages
        if len(text.split()) < 3 and not has_prev:
            intent = 'OTHER'
            difficulty = 'hard'
            needs_context = True
            confidence = 'high'
            reason = 'Extremely short text with no context'
            
        if needs_context and intent == 'OTHER' and has_prev:
            difficulty = 'hard'
            confidence = 'low'
            reason = 'Insufficient context to determine underlying intent'

        # If it's a context follow-up, mark difficulty harder
        if needs_context and intent != 'OTHER':
            difficulty = 'medium' if difficulty == 'easy' else 'hard'
            
        return intent, difficulty, needs_context, confidence, reason

    # Process and fill buckets
    for idx, row in df.iterrows():
        intent, diff, needs_ctx, conf, reason = determine_intent(row['text_clean'], row['previous_context'])
        
        if len(collected[intent]) < targets[intent]:
            # Assign example_id later
            item = {
                'tweet_id': row['tweet_id'],
                'conversation_id': row['conversation_id'],
                'customer_text': row['text_clean'],
                'previous_context': row['previous_context'],
                'intent': intent,
                'difficulty': diff,
                'needs_context': needs_ctx,
                'ai_confidence': conf,
                'review_reason': reason
            }
            collected[intent].append(item)
            
        # Stop if all targets met
        if all(len(collected[k]) == targets[k] for k in targets):
            break

    # Assemble final list
    final_items = []
    for k, v in collected.items():
        final_items.extend(v)
        
    final_df = pd.DataFrame(final_items)
    
    # Shuffle final
    final_df = final_df.sample(frac=1, random_state=123).reset_index(drop=True)
    
    # Assign example IDs
    final_df['example_id'] = [f"GOLD_{i:03d}" for i in range(1, len(final_df) + 1)]
    
    # Output Golden Set
    golden_cols = ['example_id', 'tweet_id', 'conversation_id', 'customer_text', 'previous_context', 'intent', 'difficulty', 'needs_context', 'annotation_notes']
    final_df['annotation_notes'] = ''
    golden_out = final_df[golden_cols]
    
    os.makedirs('evaluation', exist_ok=True)
    golden_out.to_csv('evaluation/golden_set.csv', index=False)
    
    # Output Review CSV
    review_cols = ['tweet_id', 'customer_text', 'previous_context', 'intent', 'difficulty', 'needs_context', 'ai_confidence', 'review_reason']
    review_out = final_df[review_cols]
    review_out.to_csv('evaluation/ai_labeling_review.csv', index=False)
    
    # Output Distribution
    dist = final_df['intent'].value_counts().reset_index()
    dist.columns = ['intent', 'count']
    dist['percentage'] = (dist['count'] / len(final_df) * 100).round(2)
    os.makedirs('results', exist_ok=True)
    dist.to_csv('results/golden_set_distribution.csv', index=False)
    
    print(f"Generated {len(final_df)} examples.")
    print("\nIntent Distribution:")
    print(dist)
    
    print("\nDifficulty:")
    print(final_df['difficulty'].value_counts())
    
    print("\nNeeds Context:")
    print(final_df['needs_context'].value_counts())
    
    print("\nConfidence:")
    print(final_df['ai_confidence'].value_counts())

if __name__ == "__main__":
    generate_balanced_set()
