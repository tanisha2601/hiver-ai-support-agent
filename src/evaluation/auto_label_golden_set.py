import pandas as pd
import re
import os

def label_golden_set():
    df = pd.read_csv('evaluation/golden_set.csv')
    
    intents = []
    difficulties = []
    needs_contexts = []
    confidences = []
    reasons = []
    
    for idx, row in df.iterrows():
        text = str(row['customer_text']).lower()
        prev = str(row['previous_context']).lower()
        has_prev = pd.notna(row['previous_context']) and row['previous_context'] != '' and row['previous_context'] != 'nan'
        
        intent = 'OTHER'
        difficulty = 'hard'
        needs_context = False
        confidence = 'low'
        reason = 'Fallback'
        
        # Determine if context is needed
        # Text is very short, or relies on pronouns, or just says "yes", "no", "done"
        if len(text.split()) <= 4 or re.search(r'^(yes|no|done|ok|okay|still waiting|i did|already did|thanks|ty|thank you)', text):
            needs_context = True
            difficulty = 'medium'
        else:
            needs_context = False
            
        full_text = text
        if needs_context and has_prev:
            full_text = text + " " + prev
            
        # Semantic Heuristics based on hierarchy
        
        # 1. DAMAGED_MISSING_ITEM (Highest priority if present)
        if re.search(r'\b(damaged|missing|broken|empty|stolen|cracked|wrong item|defective)\b', full_text):
            intent = 'DAMAGED_MISSING_ITEM'
            confidence = 'high' if re.search(r'\b(damaged|missing|broken|empty|stolen)\b', text) else 'medium'
            difficulty = 'easy' if confidence == 'high' else 'medium'
            reason = 'Matches damage/missing keywords'
            
        # 2. ACCOUNT_LOGIN
        elif re.search(r'\b(password|locked|hacked|otp|access|login|log in|email address)\b', full_text) and 'prime' not in full_text:
            intent = 'ACCOUNT_LOGIN'
            confidence = 'high' if 'locked' in text or 'password' in text else 'medium'
            difficulty = 'easy'
            reason = 'Matches account/security keywords'
            
        # 3. PAYMENT_BILLING
        elif re.search(r'\b(card|charged twice|double charge|declined|gift card|payment method|balance)\b', full_text):
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
        elif re.search(r'\b(cancel my order|change my address|update address|wrong address|change color)\b', full_text):
            intent = 'ORDER_MODIFICATION'
            confidence = 'medium'
            difficulty = 'medium'
            reason = 'Matches order modification keywords'
            
        # 5. REFUND_RETURN
        elif re.search(r'\b(refund|return|returned|money back)\b', full_text):
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
        elif re.search(r'\b(delivery|shipping|shipped|arrive|arrived|package|tracking|track|late|delayed)\b', full_text):
            intent = 'DELIVERY_SHIPPING'
            confidence = 'high'
            difficulty = 'easy'
            reason = 'Matches delivery/shipping keywords'
            
        # 7. PRIME_SUBSCRIPTION
        elif re.search(r'\b(prime|subscription|membership|renew)\b', full_text):
            intent = 'PRIME_SUBSCRIPTION'
            confidence = 'high'
            difficulty = 'easy'
            reason = 'Matches Prime keywords'
            
        # 8. CUSTOMER_SERVICE_COMPLAINT
        elif re.search(r'\b(customer service|support|chat|call|rude|hold|terrible|worst|useless|transfer)\b', text):
            intent = 'CUSTOMER_SERVICE_COMPLAINT'
            confidence = 'medium'
            difficulty = 'medium'
            reason = 'Matches complaint/frustration keywords without specific order issue'
            
        # 9. CONTEXTUAL FOLLOW UP resolving to OTHER if we still don't know
        elif needs_context and not has_prev:
            intent = 'OTHER'
            confidence = 'low'
            difficulty = 'hard'
            reason = 'Insufficient context to determine intent'
            
        else:
            intent = 'OTHER'
            confidence = 'low'
            difficulty = 'hard'
            reason = 'No distinct intent keywords found'
            
        # Special edge cases overrides
        if len(text.split()) < 3 and not has_prev:
            intent = 'OTHER'
            difficulty = 'hard'
            needs_context = True
            confidence = 'high'
            reason = 'Extremely short text with no context'
            
        intents.append(intent)
        difficulties.append(difficulty)
        needs_contexts.append(needs_context)
        confidences.append(confidence)
        reasons.append(reason)
        
    df['intent'] = intents
    df['difficulty'] = difficulties
    df['needs_context'] = needs_contexts
    
    # Validation
    allowed_intents = {
        'DELIVERY_SHIPPING', 'PRIME_SUBSCRIPTION', 'REFUND_RETURN', 'DAMAGED_MISSING_ITEM',
        'PAYMENT_BILLING', 'ACCOUNT_LOGIN', 'ORDER_MODIFICATION', 'CUSTOMER_SERVICE_COMPLAINT', 'OTHER'
    }
    assert set(df['intent'].unique()).issubset(allowed_intents), "Invalid intent found"
    assert set(df['difficulty'].unique()).issubset({'easy', 'medium', 'hard'}), "Invalid difficulty"
    assert set(df['needs_context'].unique()).issubset({True, False}), "Invalid needs_context"
    
    assert not df['intent'].isnull().any(), "Blank intent"
    assert not df['difficulty'].isnull().any(), "Blank difficulty"
    assert not df['needs_context'].isnull().any(), "Blank needs_context"
    assert len(df) == 200, "Must be exactly 200 rows"
    
    df.to_csv('evaluation/golden_set.csv', index=False)
    
    review_df = df[['tweet_id', 'customer_text', 'previous_context', 'intent', 'difficulty', 'needs_context']].copy()
    review_df['ai_confidence'] = confidences
    review_df['review_reason'] = reasons
    review_df.to_csv('evaluation/ai_labeling_review.csv', index=False)
    
    print("Labeling complete!")
    print(f"Total labeled: {len(df)}")
    print("\nIntent Distribution:")
    print(df['intent'].value_counts())
    print("\nDifficulty Distribution:")
    print(df['difficulty'].value_counts())
    print("\nNeeds Context Distribution:")
    print(df['needs_context'].value_counts())
    print("\nConfidence Distribution:")
    print(review_df['ai_confidence'].value_counts())

if __name__ == "__main__":
    label_golden_set()
