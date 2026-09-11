"""
Unit tests for the LLM-as-a-Judge evaluation engine, prompt schema, and agreement metrics.
All tests are offline and mock external API calls.
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from src.evaluation.llm_judge import (
    LLMJudge,
    MissingAPIKeyError,
    InvalidJudgeResponseError,
    LLMJudgeError
)
from src.evaluation.run_llm_judge import load_evaluation_dataset
from src.evaluation.llm_human_agreement import compute_agreement_metrics, evaluate_alignment


def test_missing_api_key_raises_actionable_error(monkeypatch):
    """Verify that calling evaluate_reply without OPENAI_API_KEY fails immediately with clear error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    judge = LLMJudge(api_key="")
    with pytest.raises(MissingAPIKeyError) as exc_info:
        judge.evaluate_reply("Where is my package?", "None", "DELIVERY_SHIPPING", "None", "On its way.")
    assert "OPENAI_API_KEY" in str(exc_info.value)
    assert "Heuristic fallbacks are strictly disabled" in str(exc_info.value)


def test_parse_and_validate_valid_json():
    """Verify schema parsing and validation on valid judge output."""
    raw_response = """```json
    {
        "relevance": 5,
        "helpfulness": 4,
        "groundedness": 5,
        "clarity": 5,
        "unsupported_claims": 5,
        "overall": 5,
        "reason": "Direct and fully grounded in evidence."
    }
    ```"""
    parsed = LLMJudge._parse_and_validate(raw_response)
    assert parsed["relevance"] == 5
    assert parsed["helpfulness"] == 4
    assert parsed["groundedness"] == 5
    assert parsed["clarity"] == 5
    assert parsed["unsupported_claims"] == 5
    assert parsed["overall"] == 5
    assert "grounded" in parsed["reason"]


def test_parse_and_validate_out_of_bounds_score():
    """Verify rejection of scores outside 1-5."""
    bad_response = """{
        "relevance": 6,
        "helpfulness": 4,
        "groundedness": 5,
        "clarity": 5,
        "unsupported_claims": 5,
        "overall": 5,
        "reason": "Out of range score."
    }"""
    with pytest.raises(InvalidJudgeResponseError) as exc_info:
        LLMJudge._parse_and_validate(bad_response)
    assert "out of bounds" in str(exc_info.value)


def test_parse_and_validate_missing_rubric_dimension():
    """Verify rejection when a rubric dimension is omitted."""
    missing_key_response = """{
        "relevance": 5,
        "groundedness": 5,
        "clarity": 5,
        "unsupported_claims": 5,
        "overall": 5,
        "reason": "Missing helpfulness key."
    }"""
    with pytest.raises(InvalidJudgeResponseError) as exc_info:
        LLMJudge._parse_and_validate(missing_key_response)
    assert "Missing required rubric dimension 'helpfulness'" in str(exc_info.value)


def test_parse_and_validate_non_json():
    """Verify rejection of non-JSON freeform responses."""
    with pytest.raises(InvalidJudgeResponseError):
        LLMJudge._parse_and_validate("This reply is pretty good, I give it 5 stars.")


def test_mocked_llm_judge_call(monkeypatch):
    """Verify full evaluation flow using a mocked API response."""
    judge = LLMJudge(api_key="mock_key_for_testing")

    mock_response = """{
        "relevance": 4,
        "helpfulness": 4,
        "groundedness": 5,
        "clarity": 5,
        "unsupported_claims": 5,
        "overall": 4,
        "reason": "Well grounded response with actionable next steps."
    }"""

    monkeypatch.setattr(judge, "_send_api_request", lambda prompt: mock_response)

    result = judge.evaluate_reply(
        customer_message="I received the wrong item in my package.",
        previous_context="None",
        predicted_intent="DAMAGED_MISSING_ITEM",
        retrieved_evidence="Historical: We will replace the wrong item.",
        generated_reply="We apologize! Please let us know the order details so we can send a replacement."
    )

    assert result["relevance"] == 4
    assert result["groundedness"] == 5
    assert result["overall"] == 4
    assert result["judge_model"] == judge.model


def test_deterministic_evaluation_dataset_loading():
    """Verify evaluation dataset loader combines context and evidence without errors."""
    df = load_evaluation_dataset()
    assert len(df) == 200
    assert "retrieved_evidence" in df.columns
    assert "previous_context" in df.columns
    assert "customer_text" in df.columns or "text" in df.columns


def test_agreement_metrics_calculation():
    """Verify statistical agreement calculations on synthetic rating vectors."""
    human = [5, 4, 3, 2, 1, 4, 5, 3]
    llm =   [5, 4, 4, 2, 1, 3, 5, 2] # 5 exact matches, all within 1 point

    metrics = compute_agreement_metrics(human, llm)
    assert metrics["n_samples"] == 8
    assert metrics["exact_agreement"] == 5 / 8 # 0.625
    assert metrics["within_1_point_agreement"] == 1.0 # 100% within 1 point
    assert abs(metrics["mean_human"] - float(np.mean(human))) < 0.01
    assert abs(metrics["mean_llm"] - float(np.mean(llm))) < 0.01
    assert metrics["spearman_correlation"] > 0.8
    assert metrics["cohen_kappa_linear_weighted"] is not None


def test_human_review_sample_file():
    """Verify human agreement sample file is correctly structured without fabricated scores."""
    review_path = "evaluation/reply_quality_human_review.csv"
    assert os.path.exists(review_path)

    df = pd.read_csv(review_path, dtype=str)
    assert len(df) == 30

    required_cols = [
        'tweet_id', 'text', 'previous_context', 'predicted_intent',
        'retrieved_evidence', 'generated_reply',
        'human_relevance', 'human_helpfulness', 'human_groundedness',
        'human_clarity', 'human_unsupported_claims', 'human_overall', 'human_notes'
    ]
    for col in required_cols:
        assert col in df.columns

    # Verify scores are genuinely unpopulated (no fake labels)
    for score_col in ['human_relevance', 'human_helpfulness', 'human_groundedness', 'human_clarity', 'human_unsupported_claims', 'human_overall']:
        empty_mask = df[score_col].isna() | (df[score_col].str.strip() == '')
        assert empty_mask.all(), f"Found unexpectedly populated scores in {score_col}!"
