# AI-Assisted Golden Evaluation Set

This document records the creation of the AI-assisted Golden Evaluation Set for the AmazonHelp intent classification project.

## 1. Important Disclaimer
**The 200 examples in `evaluation/golden_set.csv` were labeled using an AI-assisted heuristic script, NOT fully manually labeled by a human.** 
This approach was taken to expedite the project while respecting the 9-intent taxonomy. A true production golden set must be manually reviewed. This AI-assisted set serves as a strong starting point and an intermediate baseline.

## 2. Taxonomy & Labeling Rules Used
The labeling was performed strictly using the semantic intents defined in `docs/intent-taxonomy.md` and the rules outlined in `docs/labeling-guidelines.md`.

*   **Taxonomy**: The 9 core semantic intents (`DELIVERY_SHIPPING`, `PRIME_SUBSCRIPTION`, `REFUND_RETURN`, `DAMAGED_MISSING_ITEM`, `PAYMENT_BILLING`, `ACCOUNT_LOGIN`, `ORDER_MODIFICATION`, `CUSTOMER_SERVICE_COMPLAINT`, `OTHER`).
*   **Context Rule**: For short or conversational follow-ups (e.g., "Yes", "Still waiting"), the script concatenated the `previous_context` with the current message to determine the underlying semantic intent. If the intent remained unclear, it defaulted to `OTHER`.
*   **Difficulty Rule**: Clear keyword matches with long texts were marked `easy`. Complex semantic matches or context-dependent derivations were marked `medium`. Ambiguous, extremely short texts, or fallbacks were marked `hard`.

## 3. Stratification & Data Sampling Strategy
The original random sample resulted in heavy class imbalance (e.g., 0 `ORDER_MODIFICATION` and 62 `DELIVERY_SHIPPING`). 
To fix this, we implemented a targeted search across the entire 179,000+ tweet candidate pool to hunt for genuine examples of underrepresented intents, extracting them until a perfectly balanced target distribution was achieved. **No examples were fabricated or forced.**

## 4. Distribution Statistics

### Old Distribution (Random Sample)
- `DELIVERY_SHIPPING`: 62
- `OTHER`: 35
- `REFUND_RETURN`: 32
- `DAMAGED_MISSING_ITEM`: 27
- `CUSTOMER_SERVICE_COMPLAINT`: 24
- `PRIME_SUBSCRIPTION`: 18
- `ACCOUNT_LOGIN`: 1
- `PAYMENT_BILLING`: 1
- `ORDER_MODIFICATION`: 0

### New Distribution (Targeted Stratification)
Total Examples: **200**

| Intent | Count | Percentage |
| :--- | :---: | :---: |
| `OTHER` | 40 | 20.0% |
| `DELIVERY_SHIPPING` | 25 | 12.5% |
| `REFUND_RETURN` | 25 | 12.5% |
| `CUSTOMER_SERVICE_COMPLAINT` | 25 | 12.5% |
| `PRIME_SUBSCRIPTION` | 20 | 10.0% |
| `DAMAGED_MISSING_ITEM` | 20 | 10.0% |
| `ORDER_MODIFICATION` | 15 | 7.5% |
| `PAYMENT_BILLING` | 15 | 7.5% |
| `ACCOUNT_LOGIN` | 15 | 7.5% |

### Difficulty Distribution
| Difficulty | Count |
| :--- | :---: |
| `easy` | 117 |
| `medium` | 43 |
| `hard` | 40 |

### Context Dependency
| Needs Context? | Count |
| :--- | :---: |
| `False` (Self-contained) | 181 |
| `True` (Requires previous context) | 19 |

### AI Confidence Distribution
| Confidence | Count |
| :--- | :---: |
| `high` | 116 |
| `medium` | 45 |
| `low` | 39 |

## 5. Limitations & Manual Review Strategy
Because this set was generated heuristically:
1.  **Semantic Nuance**: Sarcasm or highly implicit language might be misclassified as `OTHER` or incorrectly tagged based on surface-level keywords.
2.  **Context Resolution Limits**: Heuristics are imperfect at resolving complex anaphora (e.g., "I want to cancel it" where "it" is defined in the previous message).

**Recommended Review Strategy**: 
Please review `evaluation/ai_labeling_review.csv`. Focus entirely on the 84 items marked with `low` or `medium` confidence, as well as all 40 items marked as `hard` difficulty, to quickly correct the most likely AI errors.
