"""
Agreement Metrics Evaluation: LLM Judge vs Human Expert Reviewers.

Computes:
- Mean Human Overall Score vs Mean LLM Overall Score
- Exact Agreement Rate
- Agreement within ±1
- Pearson Correlation (r)
- Spearman Rank Correlation (rho)
- Cohen's Kappa (kappa) for categorical 1-5 ratings
- Per-dimension rubric agreement analysis

Outputs:
- results/llm_human_agreement.csv
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from scipy.stats import pearsonr, spearmanr

DEFAULT_HUMAN_PATH = "evaluation/reply_quality_human_review.csv"
DEFAULT_LLM_PATH = "results/llm_judge_scores.csv"
OUTPUT_AGREEMENT_PATH = "results/llm_human_agreement.csv"

RUBRIC_MAP = {
    "overall": ("human_overall", "overall"),
    "relevance": ("human_relevance", "relevance"),
    "helpfulness": ("human_helpfulness", "helpfulness"),
    "groundedness": ("human_groundedness", "groundedness"),
    "clarity": ("human_clarity", "clarity"),
    "unsupported_claims": ("human_unsupported_claims", "unsupported_claims")
}


def compute_agreement_metrics(human_scores, llm_scores):
    """
    Computes rigorous inter-rater agreement statistics between two numeric/ordinal rating vectors.
    """
    h = np.array(human_scores, dtype=float)
    l = np.array(llm_scores, dtype=float)
    n = len(h)

    if n == 0:
        return {}

    exact_match = float(np.mean(h == l))
    adjacent_match = float(np.mean(np.abs(h - l) <= 1.0))
    mean_human = float(np.mean(h))
    mean_llm = float(np.mean(l))
    mean_diff = float(np.mean(l - h)) # positive means LLM is more lenient

    # Correlations (handle edge cases with zero variance)
    h_var = np.var(h)
    l_var = np.var(l)

    if h_var > 1e-9 and l_var > 1e-9 and n >= 3:
        try:
            pearson_val, p_p = pearsonr(h, l)
        except Exception:
            pearson_val, p_p = np.nan, np.nan
        try:
            spearman_val, p_s = spearmanr(h, l)
        except Exception:
            spearman_val, p_s = np.nan, np.nan
    else:
        pearson_val, p_p = np.nan, np.nan
        spearman_val, p_s = np.nan, np.nan

    # Cohen's Kappa for ordinal ratings
    h_cat = h.astype(int)
    l_cat = l.astype(int)
    try:
        # Linear or quadratic weighted kappa is standard for ordinal scales
        kappa_unweighted = cohen_kappa_score(h_cat, l_cat)
        kappa_weighted = cohen_kappa_score(h_cat, l_cat, weights='linear')
    except Exception:
        kappa_unweighted, kappa_weighted = np.nan, np.nan

    return {
        "n_samples": n,
        "mean_human": round(mean_human, 2),
        "mean_llm": round(mean_llm, 2),
        "mean_bias_llm_minus_human": round(mean_diff, 2),
        "exact_agreement": round(exact_match, 4),
        "within_1_point_agreement": round(adjacent_match, 4),
        "pearson_correlation": round(pearson_val, 4) if not np.isnan(pearson_val) else None,
        "spearman_correlation": round(spearman_val, 4) if not np.isnan(spearman_val) else None,
        "cohen_kappa_unweighted": round(kappa_unweighted, 4) if not np.isnan(kappa_unweighted) else None,
        "cohen_kappa_linear_weighted": round(kappa_weighted, 4) if not np.isnan(kappa_weighted) else None
    }


def evaluate_alignment(human_path=DEFAULT_HUMAN_PATH, llm_path=DEFAULT_LLM_PATH, verbose=True):
    """
    Matches human annotations with LLM judge scores by tweet_id and computes rubric alignment.
    """
    if not os.path.exists(human_path):
        raise FileNotFoundError(f"Human review file not found at '{human_path}'.")
    if not os.path.exists(llm_path):
        raise FileNotFoundError(f"LLM judge output file not found at '{llm_path}'. Please run `run_llm_judge.py` first.")

    h_df = pd.read_csv(human_path, dtype={'tweet_id': str})
    l_df = pd.read_csv(llm_path, dtype={'tweet_id': str})

    # Filter to human rows that have actually been reviewed (human_overall is non-empty)
    valid_human = h_df[h_df['human_overall'].astype(str).str.strip().ne('')].copy()

    if len(valid_human) == 0:
        msg = (
            "No completed human ratings found in 'evaluation/reply_quality_human_review.csv'.\n"
            "To review replies and establish agreement, launch the review tool:\n"
            "  python -m src.evaluation.reply_quality_reviewer\n"
        )
        if verbose:
            print(msg)
        return None, msg

    # Inner merge on tweet_id
    merged = pd.merge(valid_human, l_df, on='tweet_id', suffixes=('_human', '_llm'))
    if len(merged) == 0:
        msg = (
            f"Found {len(valid_human)} human reviews, but none matched the tweet IDs in '{llm_path}'.\n"
            "Ensure `run_llm_judge.py` evaluated the same sample of tweets."
        )
        if verbose:
            print(msg)
        return None, msg

    if verbose:
        print(f"Loaded {len(merged)} overlapping examples evaluated by both Human and LLM Judge.")

    dimension_metrics = []

    for dim_name, (h_col, l_col) in RUBRIC_MAP.items():
        if h_col in merged.columns and l_col in merged.columns:
            # Drop any missing values for this dimension
            sub = merged[[h_col, l_col]].dropna()
            sub = sub[sub[h_col].astype(str).str.strip().ne('') & sub[l_col].astype(str).str.strip().ne('')]
            if len(sub) > 0:
                h_vals = pd.to_numeric(sub[h_col], errors='coerce').dropna()
                l_vals = pd.to_numeric(sub[l_col], errors='coerce').dropna()
                valid_idx = h_vals.index.intersection(l_vals.index)
                m = compute_agreement_metrics(h_vals.loc[valid_idx], l_vals.loc[valid_idx])
                m['rubric_dimension'] = dim_name
                dimension_metrics.append(m)

    metrics_df = pd.DataFrame(dimension_metrics)
    # Reorder columns
    first_cols = ['rubric_dimension', 'n_samples', 'mean_human', 'mean_llm', 'exact_agreement', 'within_1_point_agreement', 'spearman_correlation', 'cohen_kappa_linear_weighted']
    other_cols = [c for c in metrics_df.columns if c not in first_cols]
    metrics_df = metrics_df[first_cols + other_cols]

    os.makedirs(os.path.dirname(OUTPUT_AGREEMENT_PATH), exist_ok=True)
    metrics_df.to_csv(OUTPUT_AGREEMENT_PATH, index=False)

    if verbose:
        print("\n" + "=" * 65)
        print("LLM-AS-A-JUDGE vs HUMAN AGREEMENT REPORT")
        print("=" * 65)
        ov = metrics_df[metrics_df['rubric_dimension'] == 'overall'].iloc[0] if len(metrics_df[metrics_df['rubric_dimension'] == 'overall']) > 0 else metrics_df.iloc[0]
        print(f"Sample Size (N):               {ov['n_samples']}")
        print(f"Mean Human Overall Score:      {ov['mean_human']}")
        print(f"Mean LLM Overall Score:        {ov['mean_llm']}")
        print(f"Exact Agreement (Score ==):    {ov['exact_agreement'] * 100:.1f}%")
        print(f"Within +/- 1 Agreement:        {ov['within_1_point_agreement'] * 100:.1f}%")
        print(f"Spearman Correlation (rho):    {ov.get('spearman_correlation')}")
        print(f"Cohen's Kappa (linear wt):     {ov.get('cohen_kappa_linear_weighted')}")
        print("-" * 65)
        print("Per-Dimension Breakdown:")
        for _, row in metrics_df.iterrows():
            print(f"  {row['rubric_dimension']:20s} | Exact: {row['exact_agreement']*100:4.1f}% | +/-1: {row['within_1_point_agreement']*100:4.1f}% | Human: {row['mean_human']:.2f} | LLM: {row['mean_llm']:.2f}")
        print("=" * 65)
        if ov['n_samples'] < 50:
            print("[NOTE ON STATISTICAL POWER]:")
            print(f"  The sample size (N={ov['n_samples']}) provides a directional calibration indicator.")
            print("  It is not sufficiently powered for definitive statistical significance.")
        print(f"Report saved to: {OUTPUT_AGREEMENT_PATH}")

    return metrics_df, "Success"


def main():
    parser = argparse.ArgumentParser(description="Evaluate Human vs LLM Judge Agreement")
    parser.add_argument("--human", default=DEFAULT_HUMAN_PATH, help="Path to reply_quality_human_review.csv")
    parser.add_argument("--llm", default=DEFAULT_LLM_PATH, help="Path to llm_judge_scores.csv")

    args = parser.parse_args()

    try:
        evaluate_alignment(args.human, args.llm)
    except Exception as e:
        print(f"\n[ERROR]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
