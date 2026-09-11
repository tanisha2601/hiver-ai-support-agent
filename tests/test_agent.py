import os
import pytest
from src.agent.pipeline import AgentPipeline
from src.agent.config import AgentConfig

def test_intent_classifier():
    pipeline = AgentPipeline()
    intent, conf, _ = pipeline.intent_classifier.predict("where is my package")
    assert intent == "DELIVERY_SHIPPING"
    assert 0.0 <= conf <= 1.0

def test_grounding_assessment():
    pipeline = AgentPipeline()
    assert pipeline._assess_grounding([]) == "none"
    assert pipeline._assess_grounding([{'similarity_score': 0.8}]) == "strong"
    assert pipeline._assess_grounding([{'similarity_score': 0.5}]) == "moderate"
    assert pipeline._assess_grounding([{'similarity_score': 0.2}]) == "weak"

def test_escalation_policy():
    pipeline = AgentPipeline()
    
    # Safe auto handle
    res = pipeline.escalator.decide(0.9, "strong", "DELIVERY_SHIPPING", False, 0.9)
    assert res['decision'] == "AUTO_HANDLE"
    
    # Low confidence
    res = pipeline.escalator.decide(0.4, "strong", "DELIVERY_SHIPPING", False, 0.9)
    assert res['decision'] == "ESCALATE"
    
    # Sensitive intent
    res = pipeline.escalator.decide(0.9, "strong", "ACCOUNT_LOGIN", False, 0.9)
    assert res['decision'] == "ESCALATE"
    
    # Weak grounding
    res = pipeline.escalator.decide(0.9, "weak", "DELIVERY_SHIPPING", False, 0.9)
    assert res['decision'] == "ESCALATE"

def test_e2e_pipeline():
    pipeline = AgentPipeline()
    result = pipeline.handle("My prime subscription renewed without permission.", previous_context="")
    
    assert 'tweet_id' in result
    assert 'intent' in result
    assert 'intent_confidence' in result
    assert 'generated_response' in result
    assert 'escalation_decision' in result
    
    assert result['escalation_decision'] in ["AUTO_HANDLE", "ESCALATE"]
    assert len(result['generated_response']) > 0
    assert result['intent'] in AgentConfig.VALID_INTENTS
