"""
CLI Driver to run LLM-as-a-Judge evaluation on generated customer-support replies.

Usage:
  python -m src.evaluation.run_llm_judge --limit 30 --seed 42
  python -m src.evaluation.run_llm_judge
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from src.evaluation.llm_judge import LLMJudge, MissingAPIKeyError, LLMJudgeError

DEFAULT_PREDICTIONS_PATH = "results/end_to_end_predictions.csv"
DEFAULT_GOLDEN_PATH = "evaluation/golden_set.csv"
DEFAULT_RETRIEVAL_PATH = "results/retrieval_predictions.csv"
OUTPUT_SCORES_PATH = "results/llm_judge_scores.csv"
OUTPUT_METRICS_PATH = "results/llm_judge_metrics.csv"


def load_retrieval_evidence_map(retrieval_path=DEFAULT_RETRIEVAL_PATH):
    """Builds a lookup of formatted historical support evidence per evaluation tweet ID."""
    if not os.path.exists(retrieval_path):
        return {}
    try:
        r_df = pd.read_csv(retrieval_path, dtype={'evaluation_tweet_id': str})
        evidence_map = {}
        for tweet_id, group in r_df.groupby('evaluation_tweet_id'):
            snippets = []
            for i, (_, row) in enumerate(group.head(3).iterrows(), 1):
                sim = row.get('similarity_score', 0.0)
                cust = str(row.get('retrieved_customer_text', '')).strip()
                resp = str(row.get('retrieved_historical_response', '')).strip()
                snippets.append(f"--- Example {i} (Similarity: {sim:.2f}) ---\nCustomer: {cust}\nHistorical Agent: {resp}")
            evidence_map[str(tweet_id)] = "\n\n".join(snippets)
        return evidence_map
    except Exception:
        return {}


def load_evaluation_dataset(predictions_path=DEFAULT_PREDICTIONS_PATH, golden_path=DEFAULT_GOLDEN_PATH):
    """Loads generated replies and merges conversational context and retrieved evidence."""
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(
            f"Predictions file not found at '{predictions_path}'. "
            "Please run end-to-end evaluation first to generate candidate responses."
        )

    preds_df = pd.read_csv(predictions_path, dtype={'tweet_id': str, 'conversation_id': str})

    # Merge previous context from golden set if available
    if os.path.exists(golden_path):
        gold_df = pd.read_csv(golden_path, dtype={'tweet_id': str})
        if 'previous_context' in gold_df.columns:
            ctx_map = gold_df.set_index('tweet_id')['previous_context'].fillna('').to_dict()
            preds_df['previous_context'] = preds_df['tweet_id'].map(ctx_map).fillna('')
        else:
            preds_df['previous_context'] = ''
    else:
        preds_df['previous_context'] = preds_df.get('previous_context', '')

    # Merge retrieved evidence snippets
    evidence_map = load_retrieval_evidence_map()
    preds_df['retrieved_evidence'] = preds_df['tweet_id'].map(evidence_map).fillna("No historical evidence retrieved above threshold.")

    return preds_df


def run_evaluation(limit=None, seed=42, api_key=None, base_url=None, model=None, verbose=True):
    """Executes the LLM-as-a-judge evaluation suite."""
    df = load_evaluation_dataset()

    # Deterministic sampling if limit is specified
    if limit is not None and limit < len(df):
        # Stratified sampling across predicted intents where possible
        if 'predicted_intent' in df.columns:
            sampled_dfs = []
            grouped = df.groupby('predicted_intent', group_keys=False)
            per_group = max(1, limit // max(1, df['predicted_intent'].nunique()))
            for _, group in grouped:
                sampled_dfs.append(group.sample(n=min(len(group), per_group), random_state=seed))
            sample_df = pd.concat(sampled_dfs).sample(frac=1, random_state=seed)
            if len(sample_df) < limit:
                # Fill remainder
                remainder = df[~df['tweet_id'].isin(sample_df['tweet_id'])].sample(
                    n=limit - len(sample_df), random_state=seed
                )
                sample_df = pd.concat([sample_df, remainder])
            df = sample_df.head(limit).reset_index(drop=True)
        else:
            df = df.sample(n=limit, random_state=seed).reset_index(drop=True)

    judge = LLMJudge(api_key=api_key, base_url=base_url, model=model)

    results = []
    total = len(df)
    if verbose:
        print(f"Starting LLM-as-a-Judge evaluation on {total} replies (Model: {judge.model})...")

    for i, row in df.iterrows():
        tweet_id = row['tweet_id']
        cust_text = row.get('customer_text', row.get('text', ''))
        prev_ctx = row.get('previous_context', '')
        intent = row.get('predicted_intent', 'UNKNOWN')
        evidence = row.get('retrieved_evidence', '')
        reply = row.get('generated_response', row.get('generated_reply', ''))

        if verbose and (i + 1) % 5 == 0:
            print(f"  [Evaluating {i + 1}/{total}] Tweet ID {tweet_id}...")

        try:
            scores = judge.evaluate_reply(
                customer_message=cust_text,
                previous_context=prev_ctx,
                predicted_intent=intent,
                retrieved_evidence=evidence,
                generated_reply=reply
            )
            results.append({
                'tweet_id': tweet_id,
                'customer_message': cust_text,
                'previous_context': prev_ctx,
                'predicted_intent': intent,
                'generated_reply': reply,
                'relevance': scores['relevance'],
                'helpfulness': scores['helpfulness'],
                'groundedness': scores['groundedness'],
                'clarity': scores['clarity'],
                'unsupported_claims': scores['unsupported_claims'],
                'overall': scores['overall'],
                'reason': scores['reason'],
                'judge_model': scores['judge_model'],
                'prompt_version': scores['prompt_version']
            })
        except MissingAPIKeyError:
            raise
        except LLMJudgeError as e:
            if verbose:
                print(f"  [Error evaluating tweet {tweet_id}]: {e}")
            continue

    if not results:
        raise LLMJudgeError("No examples were successfully evaluated.")

    results_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_SCORES_PATH), exist_ok=True)
    results_df.to_csv(OUTPUT_SCORES_PATH, index=False)

    # Compute Aggregate Metrics
    metrics = {
        'examples_evaluated': len(results_df),
        'mean_relevance': round(float(results_df['relevance'].mean()), 2),
        'mean_helpfulness': round(float(results_df['helpfulness'].mean()), 2),
        'mean_groundedness': round(float(results_df['groundedness'].mean()), 2),
        'mean_clarity': round(float(results_df['clarity'].mean()), 2),
        'mean_unsupported_claims': round(float(results_df['unsupported_claims'].mean()), 2),
        'mean_overall': round(float(results_df['overall'].mean()), 2),
        'judge_model': judge.model
    }

    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(OUTPUT_METRICS_PATH, index=False)

    if verbose:
        print("\n" + "=" * 55)
        print("LLM-AS-A-JUDGE REPLY QUALITY EVALUATION SUMMARY")
        print("=" * 55)
        print(f"Examples evaluated:            {metrics['examples_evaluated']}")
        print(f"Judge Model:                   {metrics['judge_model']}")
        print(f"Mean relevance (1-5):          {metrics['mean_relevance']}")
        print(f"Mean helpfulness (1-5):        {metrics['mean_helpfulness']}")
        print(f"Mean groundedness (1-5):       {metrics['mean_groundedness']}")
        print(f"Mean clarity (1-5):            {metrics['mean_clarity']}")
        print(f"Mean unsupported-claims (1-5): {metrics['mean_unsupported_claims']}")
        print(f"Mean overall score (1-5):      {metrics['mean_overall']}")
        print("=" * 55)
        print(f"Detailed scores saved to:  {OUTPUT_SCORES_PATH}")
        print(f"Aggregate metrics saved to: {OUTPUT_METRICS_PATH}")

    return results_df, metrics


def main():
    parser = argparse.ArgumentParser(description="Run LLM-as-a-Judge Reply Quality Evaluation")
    parser.add_argument("--limit", type=int, default=None, help="Sample size limit for quick testing (e.g. 30)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic sample selection")
    parser.add_argument("--model", type=str, default=None, help="Evaluation model identifier (default: gpt-4o-mini)")
    parser.add_argument("--base-url", type=str, default=None, help="OpenAI-compatible base URL")

    args = parser.parse_args()

    try:
        run_evaluation(limit=args.limit, seed=args.seed, model=args.model, base_url=args.base_url)
    except MissingAPIKeyError as e:
        print("\n[CONFIGURATION ERROR]:", e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[EVALUATION ERROR]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
