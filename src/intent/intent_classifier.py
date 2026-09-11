import os
import pandas as pd
from src.intent.classifier import IntentClassifier as BaseIntentClassifier

class IntentClassifier:
    def __init__(self, train_path='data/processed/amazon_train_pool.csv'):
        self.base_classifier = BaseIntentClassifier(train_path=train_path)
        self.allowed_intents = {
            "DELIVERY_SHIPPING",
            "PRIME_SUBSCRIPTION",
            "REFUND_RETURN",
            "DAMAGED_MISSING_ITEM",
            "PAYMENT_BILLING",
            "ACCOUNT_LOGIN",
            "ORDER_MODIFICATION",
            "CUSTOMER_SERVICE_COMPLAINT",
            "OTHER"
        }
        
    def predict_intent(self, text, context=None):
        if context:
            full_text = f"{context} {text}"
        else:
            full_text = text
            
        pred_intent, confidence, top_3 = self.base_classifier.predict(full_text)
        
        if pred_intent not in self.allowed_intents:
            pred_intent = "OTHER"
            
        return {
            "intent": pred_intent,
            "confidence": confidence,
            "method": "weak_supervision",
            "top_3": top_3
        }
