import os
import tempfile
import pandas as pd
import pytest
from src.evaluation.manual_labeler import (
    init_human_dataset,
    validate_human_dataset,
    get_progress_summary,
    VALID_INTENTS,
    VALID_DIFFICULTIES
)

def test_init_human_dataset():
    source_path = 'evaluation/golden_set.csv'
    assert os.path.exists(source_path)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "golden_set_human.csv")
        df = init_human_dataset(source_path, target_path, seed=42)
        
        assert len(df) == 200
        assert df['tweet_id'].nunique() == 200
        
        # Verify required columns exist
        required_cols = [
            'tweet_id', 'conversation_id', 'text', 'previous_context',
            'intent', 'difficulty', 'needs_context', 'annotator', 'annotation_source',
            'human_verified', 'changed_from_ai',
            'ai_suggested_intent', 'ai_suggested_difficulty', 'ai_suggested_needs_context'
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing column {col}"
            
        # Verify human verification is initially unverified (no automatic conversions)
        assert (df['human_verified'] == '').all() or df['human_verified'].isna().all()
        assert (df['annotator'] == '').all() or df['annotator'].isna().all()
        
        # Verify AI suggestions are preserved
        assert df['ai_suggested_intent'].notna().all()
        assert set(df['ai_suggested_intent'].unique()).issubset(set(VALID_INTENTS))

def test_validate_human_dataset_incomplete():
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "test_eval.csv")
        init_human_dataset('evaluation/golden_set.csv', target_path, seed=42)
        
        is_valid, errors, summary = validate_human_dataset(target_path)
        assert not is_valid
        assert summary['verified'] == 0
        assert summary['remaining'] == 200
        assert len(errors) > 0
        assert any("NOT been verified" in e for e in errors)

def test_validate_human_dataset_complete():
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "test_eval.csv")
        df = init_human_dataset('evaluation/golden_set.csv', target_path, seed=42)
        
        # Simulate human-in-the-loop review actions (both accepted and corrected)
        for i in range(len(df)):
            df.at[i, 'intent'] = VALID_INTENTS[i % len(VALID_INTENTS)]
            df.at[i, 'difficulty'] = VALID_DIFFICULTIES[i % len(VALID_DIFFICULTIES)]
            df.at[i, 'needs_context'] = "False"
            df.at[i, 'annotator'] = "reviewer_test"
            df.at[i, 'human_verified'] = "True"
            if i % 2 == 0:
                df.at[i, 'annotation_source'] = "human_verified"
                df.at[i, 'changed_from_ai'] = "False"
            else:
                df.at[i, 'annotation_source'] = "human_corrected"
                df.at[i, 'changed_from_ai'] = "True"
            
        df.to_csv(target_path, index=False)
        is_valid, errors, summary = validate_human_dataset(target_path)
        assert is_valid, f"Validation errors: {errors}"
        assert len(errors) == 0
        assert summary['verified'] == 200
        assert summary['remaining'] == 0
        assert summary['accepted'] == 100
        assert summary['corrected'] == 100
        assert all(count > 0 for count in summary['intent_distribution'].values())
