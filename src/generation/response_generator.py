import os
import json
import logging

class ResponseGenerator:
    def __init__(self, provider_type=None):
        self.provider_type = provider_type or os.getenv("LLM_PROVIDER", "dummy")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if self.provider_type == "openai" and not self.api_key:
            logging.warning("OpenAI provider selected but no API key found. Falling back to dummy generator.")
            self.provider_type = "dummy"
            
    def generate(self, customer_text, previous_context, predicted_intent, retrieved_examples):
        grounding_status, grounding_score = self._assess_grounding(retrieved_examples)
        
        prompt = self._build_prompt(customer_text, previous_context, predicted_intent, retrieved_examples)
        
        if self.provider_type == "openai":
            result = self._call_openai(prompt, retrieved_examples)
        else:
            result = self._call_dummy(customer_text, predicted_intent, retrieved_examples)
            
        result["grounding_status"] = grounding_status
        result["grounding_score"] = grounding_score
        result["confidence"] = 1.0
        return result

    def _assess_grounding(self, retrieved_examples):
        if not retrieved_examples:
            return "NONE", 0.0
            
        top_score = retrieved_examples[0].get('similarity_score', 0.0)
        
        if top_score > 0.7:
            status = "STRONG"
        elif top_score > 0.5:
            status = "MODERATE"
        elif top_score > 0.3:
            status = "WEAK"
        else:
            status = "NONE"
            
        return status, float(top_score)

    def _build_prompt(self, customer_text, previous_context, predicted_intent, retrieved_examples):
        grounding_text = ""
        for i, ex in enumerate(retrieved_examples):
            grounding_text += f"\n--- Example {i+1} ---\nCustomer: {ex['historical_customer_text']}\nAgent: {ex['historical_brand_response']}\n"
            
        return f"""
You are an expert AmazonHelp Customer Support AI.
Your task is to draft a response to the customer.

Predicted Intent: {predicted_intent}
Previous Context: {previous_context or "None"}
Current Message: {customer_text}

Historical Reference Examples (Use for tone and policy guidance, do NOT copy blindly):
{grounding_text}

Constraints:
- Address the customer's actual issue.
- Do not invent policies, refunds, dates, credits, or actions.
- Do not claim an action was performed unless the system actually performed it.
- Ask for clarification if details are missing.
- Escalate (tell the customer an agent will review) if the issue is unsafe, ambiguous, or requires account access.

Output strictly as JSON:
{{
    "response": "Your drafted reply"
}}
"""

    def _call_dummy(self, customer_text, predicted_intent, retrieved_examples):
        # A heuristic mock LLM for offline reproducible evaluation without API costs
        supporting_examples = []
        if retrieved_examples:
            supporting_examples = [ex.get('historical_tweet_id', 'unknown') for ex in retrieved_examples]
            top_res = retrieved_examples[0]['historical_brand_response']
            
            clean_res = top_res.split('^')[0] # remove agent initials
            clean_res = clean_res.replace("@115821", "") # remove generic mentions
            
            if "DM" in clean_res or "details" in clean_res or "account" in clean_res:
                response = f"{clean_res.strip()} ^AI"
            else:
                response = f"I understand your issue regarding {predicted_intent.replace('_', ' ').lower()}. {clean_res.strip()} ^AI"
        else:
            response = "I'm sorry you're experiencing this issue. Could you please provide more details so I can assist you further? ^AI"
            
        return {
            "response": response,
            "supporting_examples": supporting_examples
        }

    def _call_openai(self, prompt, retrieved_examples):
        import openai
        openai.api_key = self.api_key
        supporting_examples = [ex.get('historical_tweet_id', 'unknown') for ex in retrieved_examples] if retrieved_examples else []
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You output JSON."}, {"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = response.choices[0].message.content
            parsed = json.loads(raw)
            return {
                "response": parsed.get("response", "Error generating response"),
                "supporting_examples": supporting_examples
            }
        except Exception as e:
            return {
                "response": f"API Error: {str(e)}",
                "supporting_examples": supporting_examples
            }
