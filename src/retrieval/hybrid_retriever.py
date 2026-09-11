import os
import pandas as pd
import numpy as np
from src.retrieval.tfidf_retriever import TFIDFRetriever, weak_label
from src.retrieval.semantic_retriever import SemanticRetriever

class HybridRetriever:
    def __init__(self, alpha=0.7):
        self.alpha = alpha
        self.tfidf = TFIDFRetriever()
        self.semantic = SemanticRetriever()
        
    def retrieve(self, query_text, k=5, exclude_conversation_id=None, eval_blacklist=None):
        if not query_text or pd.isna(query_text):
            return []
            
        if eval_blacklist is None:
            eval_blacklist = set()
            
        # We need to compute hybrid scores. We can't just fetch top K from both and merge,
        # we need to fetch a broader set or compute similarity across the entire corpus.
        
        # TFIDF score computation
        query_vec_t = self.tfidf.vectorizer.transform([str(query_text).lower()])
        from sklearn.metrics.pairwise import cosine_similarity
        sim_tfidf = cosine_similarity(query_vec_t, self.tfidf.tfidf_matrix).flatten()
        
        # Semantic score computation
        if self.semantic.model is None:
            return self.tfidf.retrieve(query_text, k, exclude_conversation_id, eval_blacklist)
            
        query_vec_s = self.semantic.model.encode([str(query_text)], normalize_embeddings=True)[0]
        sim_semantic = np.dot(self.semantic.embeddings, query_vec_s)
        
        # Combine
        hybrid_scores = (self.alpha * sim_semantic) + ((1 - self.alpha) * sim_tfidf)
        
        fetch_k = min(len(hybrid_scores), k * 10)
        top_indices = np.argpartition(hybrid_scores, -fetch_k)[-fetch_k:]
        top_indices = top_indices[np.argsort(-hybrid_scores[top_indices])]
        
        results = []
        query_clean = str(query_text).strip().lower()
        
        for idx in top_indices:
            row = self.tfidf.corpus.iloc[idx]
            hist_conv_id = row['conversation_id']
            hist_text = str(row['customer_text']).strip().lower()
            
            if exclude_conversation_id and hist_conv_id == exclude_conversation_id:
                continue
            if hist_conv_id in eval_blacklist:
                continue
            if hist_text == query_clean:
                continue
                
            score = float(hybrid_scores[idx])
            
            # Additional metadata for analysis
            score_semantic = float(sim_semantic[idx])
            score_tfidf = float(sim_tfidf[idx])
            
            results.append({
                'similarity_score': score,
                'semantic_score': score_semantic,
                'tfidf_score': score_tfidf,
                'historical_customer_text': str(row['customer_text']),
                'historical_brand_response': str(row['brand_response']),
                'historical_tweet_id': str(row['tweet_id']),
                'historical_conversation_id': str(hist_conv_id),
                'retrieval_method': 'hybrid'
            })
            
            if len(results) >= k:
                break
                
        return results

def compare_retrieval_methods():
    print("Loading evaluation set...")
    eval_path = 'data/processed/amazon_eval.csv'
    eval_df = pd.read_csv(eval_path)
    
    print("Initializing retrievers...")
    methods = {
        'TF-IDF': TFIDFRetriever(),
        'Semantic': SemanticRetriever(),
        'Hybrid': HybridRetriever(alpha=0.7)
    }
    
    metrics_list = []
    
    for name, retriever in methods.items():
        print(f"\nEvaluating {name} Retriever...")
        match_at_1 = 0
        match_at_3 = 0
        match_at_5 = 0
        all_scores = []
        
        for _, row in eval_df.iterrows():
            eval_text = row['customer_text']
            gold_intent = row['intent']
            
            results = retriever.retrieve(eval_text, k=5)
            
            found_1 = False
            found_3 = False
            found_5 = False
            
            for i, res in enumerate(results):
                rank = i + 1
                all_scores.append(res['similarity_score'])
                
                hist_intent = weak_label(res['historical_customer_text'], '')
                is_match = (hist_intent == gold_intent)
                
                if is_match:
                    if rank == 1: found_1 = True
                    if rank <= 3: found_3 = True
                    if rank <= 5: found_5 = True
                    
            if found_1: match_at_1 += 1
            if found_3: match_at_3 += 1
            if found_5: match_at_5 += 1
            
        num_eval = len(eval_df)
        metrics = {
            'Method': name,
            'intent_match_at_1': match_at_1 / num_eval,
            'intent_match_at_3': match_at_3 / num_eval,
            'intent_match_at_5': match_at_5 / num_eval,
            'average_similarity': np.mean(all_scores),
            'median_similarity': np.median(all_scores)
        }
        metrics_list.append(metrics)
        print(metrics)
        
    os.makedirs('results', exist_ok=True)
    comp_df = pd.DataFrame(metrics_list)
    comp_df.to_csv('results/retrieval_method_comparison.csv', index=False)
    print("\nComparison complete. Saved to results/retrieval_method_comparison.csv")

if __name__ == "__main__":
    compare_retrieval_methods()
