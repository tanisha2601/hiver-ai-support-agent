import os
import pandas as pd
from src.retrieval.tfidf_retriever import weak_label
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

class IntentClassifier:
    def __init__(self, train_path='data/processed/amazon_train_pool.csv'):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, min_df=3, stop_words='english')
        self.clf = LogisticRegression(class_weight='balanced', max_iter=500, random_state=42)
        self.is_fitted = False
        self.train_path = train_path
        
    def fit(self, n_samples=20000):
        if not os.path.exists(self.train_path):
            raise FileNotFoundError(f"Training pool not found at {self.train_path}")
            
        print("Training Intent Classifier with weakly supervised labels...")
        train_df = pd.read_csv(self.train_path)
        train_df = train_df.sample(n=n_samples, random_state=42).reset_index(drop=True)
        
        # We use Text-Only since it performed better in our baseline evaluation (89.5% vs 86%)
        train_df['weak_intent'] = train_df.apply(lambda row: weak_label(row['text_clean'], row['previous_context']), axis=1)
        
        X_train = train_df['text_clean'].fillna('')
        y_train = train_df['weak_intent']
        
        X_train_vec = self.vectorizer.fit_transform(X_train)
        self.clf.fit(X_train_vec, y_train)
        self.is_fitted = True
        
    def predict(self, text):
        if not self.is_fitted:
            self.fit()
            
        if not text or pd.isna(text):
            return "OTHER", 0.0, []
            
        X_vec = self.vectorizer.transform([str(text).lower()])
        probs = self.clf.predict_proba(X_vec)[0]
        
        # Get top 3
        top_3_idx = probs.argsort()[-3:][::-1]
        top_3 = [{'intent': self.clf.classes_[i], 'confidence': float(probs[i])} for i in top_3_idx]
        
        pred_intent = top_3[0]['intent']
        confidence = top_3[0]['confidence']
        
        return pred_intent, confidence, top_3
