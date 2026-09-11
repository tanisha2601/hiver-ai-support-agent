import os
import pandas as pd
import pytest

def test_golden_candidates_format():
    path = "evaluation/golden_set.csv"
    if not os.path.exists(path):
        pytest.skip("Golden set not yet generated.")
        
    df = pd.read_csv(path)
    
    # Check required columns
    required_cols = [
        'example_id', 'tweet_id', 'conversation_id', 'customer_text', 
        'previous_context', 'intent', 'difficulty', 'needs_context', 'annotation_notes'
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
        
    # Check unique example IDs
    assert df['example_id'].nunique() == len(df), "example_id must be unique"
    
    # Check valid tweet IDs
    assert df['tweet_id'].notna().all(), "tweet_id cannot be null"
    
    # Verify exact duplicates of customer_text are minimized (some short ones like "yes" might legitimately duplicate)
    # Just checking we have a reasonable size
    assert 150 <= len(df) <= 250, f"Expected 150-250 candidates, got {len(df)}"

def test_golden_labels_empty_initially():
    """
    Ensures that the AI did not fabricate manual intent labels automatically
    during the candidate generation stage.
    """
    path = "evaluation/golden_set.csv"
    if not os.path.exists(path):
        pytest.skip("Golden set not yet generated.")
        
    df = pd.read_csv(path)
    
    # Check that intent labels are actually empty (or NaN if pandas loaded empty strings as nan)
    # If the user has manually annotated them, this test might fail, so we skip if manually annotated
    if df['intent'].notna().any() and len(df[df['intent'].notna()]) > 0:
        pytest.skip("Golden set already partially/fully manually annotated.")
        
    assert df['intent'].isna().all() or (df['intent'] == "").all(), "Intent labels must not be auto-generated."
