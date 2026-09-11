import os

class AgentConfig:
    # Retrieval configuration
    HYBRID_ALPHA = float(os.getenv("AGENT_HYBRID_ALPHA", "0.7"))  # 0.7 Semantic, 0.3 TF-IDF
    RETRIEVAL_K = int(os.getenv("AGENT_RETRIEVAL_K", "5"))
    
    # Embedding configuration
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Grounding status thresholds
    GROUNDING_STRONG_THRESHOLD = 0.65
    GROUNDING_MODERATE_THRESHOLD = 0.40
    
    # Escalation policy thresholds
    INTENT_CONFIDENCE_THRESHOLD = 0.50
    
    # Intent taxonomy
    VALID_INTENTS = {
        'DELIVERY_SHIPPING', 'PRIME_SUBSCRIPTION', 'REFUND_RETURN', 'DAMAGED_MISSING_ITEM',
        'PAYMENT_BILLING', 'ACCOUNT_LOGIN', 'ORDER_MODIFICATION', 'CUSTOMER_SERVICE_COMPLAINT', 'OTHER'
    }
    
    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "dummy") # 'dummy' or 'openai'
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
