"""
LLM-as-a-Judge Evaluation Engine for Customer Support Replies.

Evaluates generated customer support responses against a strict 1-5 rubric across:
- Relevance
- Helpfulness
- Groundedness
- Clarity
- Unsupported Claims / Hallucination
- Overall Score
"""

import os
import json
import time
import urllib.request
import urllib.error
from src.evaluation.prompts import (
    LLM_JUDGE_SYSTEM_PROMPT,
    LLM_JUDGE_USER_PROMPT_TEMPLATE,
    LLM_JUDGE_PROMPT_VERSION
)

REQUIRED_SCORE_KEYS = [
    "relevance",
    "helpfulness",
    "groundedness",
    "clarity",
    "unsupported_claims",
    "overall"
]


class LLMJudgeError(Exception):
    """Base exception for LLM Judge evaluation errors."""
    pass


class MissingAPIKeyError(LLMJudgeError):
    """Raised when OPENAI_API_KEY is not configured."""
    pass


class InvalidJudgeResponseError(LLMJudgeError):
    """Raised when the LLM returns unparseable or out-of-rubric outputs."""
    pass


class LLMJudge:
    def __init__(self, api_key=None, base_url=None, model=None, max_retries=3, retry_delay=1.5):
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _validate_api_key(self):
        if not self.api_key:
            raise MissingAPIKeyError(
                "Missing required environment variable 'OPENAI_API_KEY'. "
                "Please configure OPENAI_API_KEY in your environment or .env file before running the LLM judge. "
                "Note: Heuristic fallbacks are strictly disabled for genuine LLM evaluation."
            )

    def evaluate_reply(self, customer_message, previous_context, predicted_intent, retrieved_evidence, generated_reply):
        """
        Submits a single customer support reply to the LLM judge for evaluation.
        Does NOT expose reference/gold ratings to prevent evaluation bias.
        """
        self._validate_api_key()

        user_prompt = LLM_JUDGE_USER_PROMPT_TEMPLATE.format(
            customer_message=str(customer_message or "None"),
            conversation_context=str(previous_context or "None (Self-contained)"),
            predicted_intent=str(predicted_intent or "UNKNOWN"),
            retrieved_evidence=str(retrieved_evidence or "None provided"),
            generated_reply=str(generated_reply or "")
        )

        raw_response = self._call_llm_with_retry(user_prompt)
        parsed = self._parse_and_validate(raw_response)
        parsed["judge_model"] = self.model
        parsed["prompt_version"] = LLM_JUDGE_PROMPT_VERSION
        return parsed

    def _call_llm_with_retry(self, user_prompt):
        """Dispatches the completion request with exponential backoff on transient errors."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return self._send_api_request(user_prompt)
            except Exception as e:
                last_exception = e
                # Check for fatal auth errors (401/403) to avoid futile retries
                err_str = str(e).lower()
                if "401" in err_str or "unauthorized" in err_str or "forbidden" in err_str:
                    raise LLMJudgeError(f"API Authentication Failed: {e}") from e

                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2 ** attempt)
                    time.sleep(sleep_time)

        raise LLMJudgeError(f"LLM Judge request failed after {self.max_retries} attempts: {last_exception}") from last_exception

    def _send_api_request(self, user_prompt):
        """
        Sends an HTTP POST to the OpenAI-compatible chat completion endpoint.
        Uses standard urllib to avoid version conflicts with external client libraries.
        Can be easily mocked or monkeypatched in tests.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": LLM_JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8")
                res_json = json.loads(body)
                return res_json["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
            raise LLMJudgeError(f"HTTP Error {e.code}: {err_msg}") from e
        except urllib.error.URLError as e:
            raise LLMJudgeError(f"Network Connection Error: {e.reason}") from e

    @staticmethod
    def _parse_and_validate(raw_text):
        """
        Parses JSON response and strictly verifies score ranges (1-5) and required keys.
        """
        if not raw_text or not isinstance(raw_text, str):
            raise InvalidJudgeResponseError(f"Judge returned empty or non-string response: {raw_text}")

        # Strip markdown code blocks if present
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError as e:
            raise InvalidJudgeResponseError(f"Judge output is not valid JSON: {raw_text}") from e

        if not isinstance(data, dict):
            raise InvalidJudgeResponseError(f"Judge output must be a JSON dictionary, got {type(data)}")

        # Validate required score keys
        for key in REQUIRED_SCORE_KEYS:
            if key not in data:
                raise InvalidJudgeResponseError(f"Missing required rubric dimension '{key}' in output: {data}")

            val = data[key]
            # Must be integer or convertible to int 1-5
            try:
                int_val = int(val)
            except (ValueError, TypeError):
                raise InvalidJudgeResponseError(f"Rubric dimension '{key}' value '{val}' is not a valid integer.")

            if not (1 <= int_val <= 5):
                raise InvalidJudgeResponseError(f"Rubric dimension '{key}' score {int_val} out of bounds (must be 1-5).")

            data[key] = int_val

        # Validate reason
        if "reason" not in data or not str(data["reason"]).strip():
            data["reason"] = "No explanation provided by judge."
        else:
            data["reason"] = str(data["reason"]).strip()

        return data
