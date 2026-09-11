"""
Prompt templates for LLM-as-a-Judge reply quality evaluation.
"""

LLM_JUDGE_PROMPT_VERSION = "1.0.0"

LLM_JUDGE_SYSTEM_PROMPT = """You are an expert AI evaluator assessing the quality of customer-support responses for an automated support agent.
You evaluate responses strictly according to defined rubrics and return structured JSON output."""

LLM_JUDGE_USER_PROMPT_TEMPLATE = """You are evaluating the quality of an AI customer-support reply.

Judge ONLY the reply using the customer message, conversation context, predicted intent and retrieved historical evidence supplied to you.

Do not reward a response merely because it sounds professional.

Penalize:
- irrelevant answers
- unsupported promises
- invented policies
- invented refund/return decisions
- invented timelines
- claims that an action was completed when the evidence does not show it
- failure to acknowledge ambiguity or missing context

Groundedness means that the response is supported by the provided evidence, not that it sounds plausible.

--------------------------------------------------
EVALUATION INPUTS
--------------------------------------------------
Customer Message:
{customer_message}

Previous Conversation Context:
{conversation_context}

Predicted Intent:
{predicted_intent}

Retrieved Historical Evidence:
{retrieved_evidence}

Generated Reply Under Evaluation:
{generated_reply}

--------------------------------------------------
SCORING RUBRIC (Score each dimension 1 to 5)
--------------------------------------------------
1. Relevance:
   5 = Directly addresses the customer's actual issue
   4 = Mostly addresses the issue with minor irrelevant content
   3 = Partially addresses the issue
   2 = Weakly related or misses an important part
   1 = Does not address the customer's issue

2. Helpfulness:
   5 = Gives a clear, useful, and actionable response
   4 = Useful but missing a minor detail
   3 = Somewhat useful but incomplete
   2 = Vague or minimally useful
   1 = Not useful

3. Groundedness:
   5 = Claims and recommended actions are strongly supported by the provided historical evidence/context
   4 = Mostly grounded with minor unsupported wording
   3 = Mixed grounding
   2 = Significant unsupported claims
   1 = Largely unsupported or contradictory

4. Clarity:
   5 = Concise, clear, and easy to understand
   4 = Clear with minor verbosity
   3 = Understandable but somewhat verbose/confusing
   2 = Difficult to follow
   1 = Unclear

5. Unsupported Claims / Hallucination:
   5 = No unsupported claims
   4 = Very minor unsupported wording
   3 = One questionable claim
   2 = Multiple unsupported claims
   1 = Substantial fabrication

Overall Score (1 to 5):
Synthesize the above dimensions into an overall rating from 1 (unacceptable) to 5 (excellent).

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------
Return ONLY a valid JSON object with the following exact keys:
{{
  "relevance": <int 1-5>,
  "helpfulness": <int 1-5>,
  "groundedness": <int 1-5>,
  "clarity": <int 1-5>,
  "unsupported_claims": <int 1-5>,
  "overall": <int 1-5>,
  "reason": "<short explanation, 1-3 sentences>"
}}
"""
