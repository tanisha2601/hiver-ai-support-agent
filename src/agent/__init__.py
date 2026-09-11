import os
from src.intent.intent_classifier import IntentClassifier
from src.retrieval.hybrid_retriever import HybridRetriever
from src.generation.response_generator import ResponseGenerator
from src.escalation.escalation_policy import EscalationPolicy

# Cache instances so we don't reload models every call if used in a loop
_intent_classifier = None
_retriever = None
_generator = None
_escalator = None

def _get_components():
    global _intent_classifier, _retriever, _generator, _escalator
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    if _retriever is None:
        _retriever = HybridRetriever(alpha=0.7)
    if _generator is None:
        _generator = ResponseGenerator()
    if _escalator is None:
        _escalator = EscalationPolicy()
    return _intent_classifier, _retriever, _generator, _escalator

def run_agent(customer_message, context=None, exclude_conversation_id=None, eval_blacklist=None):
    """
    Run the end-to-end AI Customer Support Agent pipeline.
    """
    intent_classifier, retriever, generator, escalator = _get_components()
    
    # 1. Intent classification
    intent_result = intent_classifier.predict_intent(customer_message, context)
    intent = intent_result['intent']
    intent_confidence = intent_result['confidence']
    
    # 2. Retrieval
    full_text = customer_message
    if context:
        full_text = f"{context} {customer_message}"
        
    retrieved_examples = retriever.retrieve(
        full_text, 
        k=5, 
        exclude_conversation_id=exclude_conversation_id, 
        eval_blacklist=eval_blacklist
    )
    
    # 3. Response Generation (which also assesses grounding)
    gen_result = generator.generate(customer_message, context, intent, retrieved_examples)
    
    # Determine context need for escalation
    words = str(customer_message).split()
    needs_context = len(words) <= 4 and not context
    
    # 4. Escalation Decision
    esc_result = escalator.decide(
        intent_confidence=intent_confidence,
        grounding_status=gen_result['grounding_status'],
        predicted_intent=intent,
        needs_context=needs_context
    )
    
    # 5. Output
    return {
        "customer_message": customer_message,
        "intent": intent,
        "intent_confidence": intent_confidence,
        "retrieved_examples": retrieved_examples,
        "grounding_status": gen_result['grounding_status'],
        "grounding_score": gen_result['grounding_score'],
        "response": gen_result['response'],
        "decision": esc_result['decision'],
        "decision_reason": esc_result['escalation_reason']
    }
