from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AgentRequest(BaseModel):
    message: str = Field(..., description="The customer's message to analyze.")
    context: Optional[str] = Field(None, description="Optional previous context/conversation.")

class RetrievedExample(BaseModel):
    historical_customer_text: str
    historical_brand_response: str
    similarity_score: float
    retrieval_method: str

class AgentResponse(BaseModel):
    customer_message: str
    intent: str
    intent_confidence: float
    retrieved_examples: List[Dict[str, Any]]
    grounding_status: str
    grounding_score: float
    response: str
    decision: str
    decision_reason: str
