import os
import pickle
import pandas as pd
import numpy as np

class SemanticRetriever:
    def __init__(self, index_dir='data/processed/retrieval'):
        self.index_dir = index_dir
        self.embeddings = None
        self.corpus = None
        self.model = None
        self._load_index()
        
    def _load_index(self):
        emb_path = os.path.join(self.index_dir, 'semantic_embeddings.pkl')
        corp_path = os.path.join(self.index_dir, 'corpus_lookup.pkl')
        
        if not os.path.exists(emb_path) or not os.path.exists(corp_path):
            print("Warning: Retrieval index artifacts not fully found. Semantic retrieval disabled.")
            return
            
        with open(emb_path, 'rb') as f:
            self.embeddings = pickle.load(f)
            
        self.corpus = pd.read_pickle(corp_path)
        
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            print("Warning: sentence_transformers not available. Semantic retrieval will fail.")
            
    def retrieve(self, query_text, k=5, exclude_conversation_id=None, eval_blacklist=None):
        if not query_text or pd.isna(query_text) or self.model is None or self.embeddings is None:
            return []
            
        if eval_blacklist is None:
            eval_blacklist = set()
            
        query_vec = self.model.encode([str(query_text)], normalize_embeddings=True)[0]
        
        # Calculate dot product (cosine similarity for normalized vectors)
        similarities = np.dot(self.embeddings, query_vec)
        
        # We fetch more than K because we might filter some out
        fetch_k = min(len(similarities), k * 10)
        top_indices = np.argpartition(similarities, -fetch_k)[-fetch_k:]
        top_indices = top_indices[np.argsort(-similarities[top_indices])]
        
        results = []
        query_clean = str(query_text).strip().lower()
        
        for idx in top_indices:
            row = self.corpus.iloc[idx]
            hist_conv_id = row['conversation_id']
            hist_text = str(row['customer_text']).strip().lower()
            
            # Filtering conditions
            if exclude_conversation_id and hist_conv_id == exclude_conversation_id:
                continue
            if hist_conv_id in eval_blacklist:
                continue
            if hist_text == query_clean:
                continue
                
            score = float(similarities[idx])
            results.append({
                'similarity_score': score,
                'historical_customer_text': row['customer_text'],
                'historical_brand_response': row['brand_response'],
                'historical_tweet_id': row['tweet_id'],
                'historical_conversation_id': hist_conv_id,
                'retrieval_method': 'semantic'
            })
            
            if len(results) >= k:
                break
                
        return results
