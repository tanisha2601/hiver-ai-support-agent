class EscalationPolicy:
    def __init__(self, config=None):
        self.intent_thresh = getattr(config, 'INTENT_CONFIDENCE_THRESHOLD', 0.50) if config else 0.50
        
    def decide(self, intent_confidence, grounding_status, predicted_intent, needs_context, gen_confidence=1.0):
        signals = {
            "low_intent_confidence": intent_confidence < self.intent_thresh,
            "weak_grounding": grounding_status.upper() in ['WEAK', 'NONE'],
            "needs_context": needs_context,
            "sensitive_intent": predicted_intent in ['ACCOUNT_LOGIN', 'PAYMENT_BILLING'],
            "serious_complaint": predicted_intent == 'CUSTOMER_SERVICE_COMPLAINT',
            "unsupported_action": predicted_intent in ['ORDER_MODIFICATION', 'REFUND_RETURN'] and grounding_status.upper() != 'STRONG',
            "low_generation_confidence": gen_confidence < 0.6
        }
        
        decision = "AUTO_HANDLE"
        reason = "All signals confident and safe."
        
        if signals["sensitive_intent"]:
            decision = "ESCALATE"
            reason = f"Intent {predicted_intent} requires account-specific action."
        elif signals["serious_complaint"]:
            decision = "ESCALATE"
            reason = "Serious customer complaint detected."
        elif signals["low_intent_confidence"]:
            decision = "ESCALATE"
            reason = f"Intent confidence {intent_confidence:.2f} below threshold."
        elif signals["weak_grounding"]:
            decision = "ESCALATE"
            reason = "Weak or no historical grounding found."
        elif signals["needs_context"]:
            decision = "ESCALATE"
            reason = "Unclear context, follow-up needed."
        elif signals["unsupported_action"]:
            decision = "ESCALATE"
            reason = f"Action for {predicted_intent} requires strong grounding or is unsupported."
        elif signals["low_generation_confidence"]:
            decision = "ESCALATE"
            reason = "Generator confidence too low."
            
        return {
            "decision": decision,
            "escalation_reason": reason,
            "policy_signals": signals,
            "confidence": 1.0 if decision == "ESCALATE" else intent_confidence
        }
