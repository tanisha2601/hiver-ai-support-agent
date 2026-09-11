import os
import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

def build_retrieval_index():
    print("Loading datasets...")
    pool_path = 'data/processed/amazon_train_pool.csv'
    raw_path = 'data/raw/twcs.csv'
    
    if not os.path.exists(pool_path) or not os.path.exists(raw_path):
        print("Required datasets not found.")
        return
        
    pool_df = pd.read_csv(pool_path)
    raw_df = pd.read_csv(raw_path, dtype={'tweet_id': str, 'response_tweet_id': str, 'in_response_to_tweet_id': str})
    
    print("Extracting brand responses...")
    # Map tweet_id -> its response_tweet_id(s)
    # response_tweet_id can be a comma separated list, we just take the first one for simplicity, or just match against in_response_to_tweet_id
    
    # We want AmazonHelp responses. AmazonHelp is author_id 'AmazonHelp'.
    amazon_responses = raw_df[raw_df['author_id'] == 'AmazonHelp']
    # A customer tweet is answered by an AmazonHelp tweet if AmazonHelp's in_response_to_tweet_id == customer's tweet_id
    
    # Create a mapping from customer_tweet_id -> brand_response_text
    response_map = amazon_responses.set_index('in_response_to_tweet_id')['text'].to_dict()
    
    # Add brand response to the pool
    pool_df['tweet_id'] = pool_df['tweet_id'].astype(str)
    pool_df['brand_response'] = pool_df['tweet_id'].map(response_map)
    
    # Filter to only those with a genuine brand response
    valid_pool = pool_df[pool_df['brand_response'].notna()].copy()
    valid_pool['customer_text'] = valid_pool['text_clean'].fillna('')
    print(f"Found {len(valid_pool)} valid customer->brand pairs out of {len(pool_df)} pool messages.")
    
    # Ensure no leakage in valid_pool by verifying against golden eval just in case
    eval_path = 'data/processed/amazon_eval.csv'
    eval_df = pd.read_csv(eval_path, dtype={'conversation_id': str})
    eval_convs = set(eval_df['conversation_id'].unique())
    valid_pool = valid_pool[~valid_pool['conversation_id'].astype(str).isin(eval_convs)].copy()
    
    print("Building TF-IDF index...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        lowercase=True,
        min_df=3,
        max_features=50000,
        stop_words='english',
        norm='l2'
    )
    
    tfidf_matrix = vectorizer.fit_transform(valid_pool['customer_text'])
    
    # Save artifacts
    os.makedirs('data/processed/retrieval', exist_ok=True)
    
    with open('data/processed/retrieval/tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
        
    with open('data/processed/retrieval/tfidf_matrix.pkl', 'wb') as f:
        pickle.dump(tfidf_matrix, f)
        
    print("Building Semantic index...")
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        print("Loading sentence-transformers model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        # We process in batches to save memory
        texts = valid_pool['customer_text'].tolist()
        print("Encoding semantic vectors...")
        embeddings = model.encode(texts, batch_size=256, show_progress_bar=True, normalize_embeddings=True)
        
        with open('data/processed/retrieval/semantic_embeddings.pkl', 'wb') as f:
            pickle.dump(embeddings, f)
            
        print("Semantic index built successfully.")
    except Exception as e:
        print(f"Warning: Failed to build semantic index. Semantic retrieval will be disabled. Error: {e}")

    # Save the lookup table
    lookup_cols = ['tweet_id', 'conversation_id', 'customer_text', 'brand_response']
    valid_pool[lookup_cols].to_pickle('data/processed/retrieval/corpus_lookup.pkl')
    
    print("Indices built successfully.")
    
if __name__ == "__main__":
    build_retrieval_index()
