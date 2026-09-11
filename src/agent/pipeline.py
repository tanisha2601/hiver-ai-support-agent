import os
from src.agent.config import AgentConfig
from src.intent.classifier import IntentClassifier
from src.retrieval.hybrid_retriever import HybridRetriever
from src.generation.response_generator import ResponseGenerator
from src.escalation.escalation_policy import EscalationPolicy

class AgentPipeline:
    def __init__(self, config=AgentConfig):
        self.config = config
        self.intent_classifier = IntentClassifier()
        self.retriever = HybridRetriever(alpha=config.HYBRID_ALPHA)
        self.generator = ResponseGenerator(provider_type=config.LLM_PROVIDER)
        self.escalator = EscalationPolicy(config=config)
        
    def _assess_grounding(self, retrieved_examples):
        if not retrieved_examples:
            return "none"
            
        top_score = retrieved_examples[0]['similarity_score']
        
        if top_score >= self.config.GROUNDING_STRONG_THRESHOLD:
            return "strong"
        elif top_score >= self.config.GROUNDING_MODERATE_THRESHOLD:
            return "moderate"
        else:
            return "weak"

    def handle(self, customer_text, previous_context=None, tweet_id=None):
        # 1. Intent Classification
        pred_intent, intent_conf, top_3 = self.intent_classifier.predict(customer_text)
        
        # Determine if context was needed (proxy check)
        needs_context = False
        words = str(customer_text).split()
        if len(words) <= 4:
            needs_context = True
            
        # 2. Retrieval
        retrieved_examples = self.retriever.retrieve(customer_text, k=self.config.RETRIEVAL_K)
        
        # 3. Grounding Assessment
        grounding_status = self._assess_grounding(retrieved_examples)
        
        # 4. Response Generation
        gen_result = self.generator.generate(customer_text, previous_context, pred_intent, retrieved_examples)
        
        # 5. Escalation Decision
        esc_result = self.escalator.decide(
            intent_confidence=intent_conf,
            grounding_status=grounding_status,
            predicted_intent=pred_intent,
            needs_context=needs_context,
            gen_confidence=gen_result['confidence']
        )
        
        # 6. Structured Output
        return {
            "tweet_id": tweet_id,
            "customer_text": customer_text,
            "intent": pred_intent,
            "intent_confidence": intent_conf,
            "retrieval_method": "hybrid" if retrieved_examples and retrieved_examples[0].get('retrieval_method') == 'hybrid' else "mixed",
            "top_retrieval_score": retrieved_examples[0]['similarity_score'] if retrieved_examples else 0.0,
            "retrieved_examples": [ex['historical_tweet_id'] for ex in retrieved_examples],
            "grounding_status": grounding_status,
            "generated_response": gen_result['response'],
            "escalation_decision": esc_result['decision'],
            "escalation_reason": esc_result['escalation_reason'],
            "overall_confidence": min(intent_conf, gen_result['confidence'])
        }

if __name__ == "__main__":
    agent = AgentPipeline()
    res = agent.handle("Where is my package? It was supposed to be here yesterday.", previous_context="")
    import json
    print(json.dumps(res, indent=2))
