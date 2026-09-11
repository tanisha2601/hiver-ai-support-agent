import os
import pickle
import pandas as pd
import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity

class TFIDFRetriever:
    def __init__(self, index_dir='data/processed/retrieval'):
        self.index_dir = index_dir
        self.vectorizer = None
        self.tfidf_matrix = None
        self.corpus = None
        self._load_index()
        
    def _load_index(self):
        vec_path = os.path.join(self.index_dir, 'tfidf_vectorizer.pkl')
        mat_path = os.path.join(self.index_dir, 'tfidf_matrix.pkl')
        corp_path = os.path.join(self.index_dir, 'corpus_lookup.pkl')
        
        if not os.path.exists(vec_path) or not os.path.exists(mat_path) or not os.path.exists(corp_path):
            raise FileNotFoundError("Retrieval index artifacts not found. Please run build_index.py first.")
            
        with open(vec_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
            
        with open(mat_path, 'rb') as f:
            self.tfidf_matrix = pickle.load(f)
            
        self.corpus = pd.read_pickle(corp_path)
        
    def retrieve(self, query_text, k=5, exclude_conversation_id=None, eval_blacklist=None):
        if not query_text or pd.isna(query_text):
            return []
            
        if eval_blacklist is None:
            eval_blacklist = set()
            
        query_vec = self.vectorizer.transform([str(query_text).lower()])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Fetch more since we filter
        fetch_k = min(len(similarities), k * 10)
        top_indices = np.argpartition(similarities, -fetch_k)[-fetch_k:]
        top_indices = top_indices[np.argsort(-similarities[top_indices])]
        
        results = []
        query_clean = str(query_text).strip().lower()
        
        for idx in top_indices:
            row = self.corpus.iloc[idx]
            hist_conv_id = row['conversation_id']
            hist_text = str(row['customer_text']).strip().lower()
            
            if exclude_conversation_id and hist_conv_id == exclude_conversation_id:
                continue
            if hist_conv_id in eval_blacklist:
                continue
            if hist_text == query_clean:
                continue
                
            score = float(similarities[idx])
            results.append({
                'similarity_score': score,
                'historical_customer_text': str(row['customer_text']),
                'historical_brand_response': str(row['brand_response']),
                'historical_tweet_id': str(row['tweet_id']),
                'historical_conversation_id': str(hist_conv_id)
            })
            
            if len(results) >= k:
                break
                
        return results

def weak_label(text, prev):
    # Proxy intent labeler for evaluation against historical corpus
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
        if 'prime' in full_text: return 'PRIME_SUBSCRIPTION'
        else: return 'PAYMENT_BILLING'
    elif re.search(r'\b(cancel order|cancel my order|change my address|update address|wrong address|change color|change size|wrong size|modify order|cancel this order)\b', full_text):
        return 'ORDER_MODIFICATION'
    elif re.search(r'\b(refund|return|returned|money back|returning)\b', full_text):
        if 'prime' in full_text and 'membership' in full_text: return 'PRIME_SUBSCRIPTION'
        else: return 'REFUND_RETURN'
    elif re.search(r'\b(delivery|shipping|shipped|arrive|arrived|package|tracking|track|late|delayed|where is my)\b', full_text):
        return 'DELIVERY_SHIPPING'
    elif re.search(r'\b(prime|subscription|membership|renew|subscribe)\b', full_text):
        return 'PRIME_SUBSCRIPTION'
    elif re.search(r'\b(customer service|support|chat|call|rude|hold|terrible|worst|useless|transfer|on hold)\b', text):
        return 'CUSTOMER_SERVICE_COMPLAINT'
    else:
        return 'OTHER'

def evaluate_retrieval():
    print("Loading evaluation set...")
    eval_path = 'data/processed/amazon_eval.csv'
    eval_df = pd.read_csv(eval_path)
    
    print("Initializing retriever...")
    retriever = TFIDFRetriever()
    
    predictions = []
    
    match_at_1 = 0
    match_at_3 = 0
    match_at_5 = 0
    
    all_scores = []
    
    for _, row in eval_df.iterrows():
        eval_id = row['tweet_id']
        eval_conv_id = row['conversation_id']
        eval_text = row['customer_text']
        gold_intent = row['intent']
        
        # We retrieve top 5 so we can evaluate @1, @3, @5 in one pass
        results = retriever.retrieve(eval_text, k=5)
        
        # Track matches for this query
        found_match_at_1 = False
        found_match_at_3 = False
        found_match_at_5 = False
        
        for i, res in enumerate(results):
            rank = i + 1
            all_scores.append(res['similarity_score'])
            
            # Proxy intent match
            hist_intent = weak_label(res['historical_customer_text'], '')
            is_match = (hist_intent == gold_intent)
            
            if is_match:
                if rank == 1: found_match_at_1 = True
                if rank <= 3: found_match_at_3 = True
                if rank <= 5: found_match_at_5 = True
                
            predictions.append({
                'evaluation_tweet_id': eval_id,
                'evaluation_conversation_id': eval_conv_id,
                'customer_text': eval_text,
                'gold_intent': gold_intent,
                'retrieved_rank': rank,
                'similarity_score': res['similarity_score'],
                'retrieved_customer_text': res['historical_customer_text'],
                'retrieved_historical_response': res['historical_brand_response'],
                'retrieved_conversation_id': res['historical_conversation_id']
            })
            
        if found_match_at_1: match_at_1 += 1
        if found_match_at_3: match_at_3 += 1
        if found_match_at_5: match_at_5 += 1
        
    num_eval = len(eval_df)
    
    # Calculate final metrics
    metrics = {
        'intent_match_at_1': match_at_1 / num_eval,
        'intent_match_at_3': match_at_3 / num_eval,
        'intent_match_at_5': match_at_5 / num_eval,
        'average_similarity': np.mean(all_scores),
        'median_similarity': np.median(all_scores)
    }
    
    # Save outputs
    os.makedirs('results', exist_ok=True)
    pd.DataFrame(predictions).to_csv('results/retrieval_predictions.csv', index=False)
    pd.DataFrame([metrics]).to_csv('results/retrieval_metrics.csv', index=False)
    
    print("\nRetrieval Evaluation Results:")
    print(f"Intent Match @1: {metrics['intent_match_at_1']:.4f}")
    print(f"Intent Match @3: {metrics['intent_match_at_3']:.4f}")
    print(f"Intent Match @5: {metrics['intent_match_at_5']:.4f}")
    print(f"Average Similarity: {metrics['average_similarity']:.4f}")
    print(f"Median Similarity: {metrics['median_similarity']:.4f}")

if __name__ == "__main__":
    evaluate_retrieval()
