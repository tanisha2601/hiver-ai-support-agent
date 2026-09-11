# Intent Classification Baselines

This document tracks the performance of baseline models evaluated against the `AmazonHelp` Golden Evaluation Set (`amazon_eval.csv`).

## 1. Majority-Class Baseline

### Overview
The Majority-Class Baseline is the simplest possible classification model. It calculates the most frequent intent in the training data and blindly predicts that exact same intent for every single evaluation example, regardless of the text.

### How the Majority Intent is Determined
Because the `amazon_train_pool.csv` dataset is currently unlabeled, the majority intent was estimated using a fast heuristic keyword scan across the entire 178,245-row training pool. This confirmed that **`DELIVERY_SHIPPING`** is the dominant intent class in the underlying data distribution.

### Why it is Intentionally Simple
The purpose of a majority baseline is not to solve the problem, but to establish a statistical floor. It answers the question: *"What accuracy would a model achieve if it learned absolutely nothing about language, and simply guessed the most common category every time?"*

### Why it Provides a Useful Lower Bound
In highly imbalanced datasets, accuracy can be misleading. If 90% of customers ask about shipping, a model that only predicts `DELIVERY_SHIPPING` will achieve 90% accuracy while having a Macro F1 score near 0. By calculating the majority baseline, we have a concrete lower bound for Accuracy and Macro F1 that any subsequent machine learning model (like Logistic Regression or an LLM) MUST beat to prove it is actually learning semantic patterns.

### Final Metrics
*   **Majority Intent**: `DELIVERY_SHIPPING`
*   **Accuracy**: 12.50%
*   **Macro F1**: 0.0247
*   **Weighted F1**: 0.0278

## 2. TF-IDF + Logistic Regression Baseline

### Overview
This baseline establishes a strong, traditional machine learning benchmark using classical natural language processing. It uses TF-IDF (Term Frequency-Inverse Document Frequency) vectorization of word unigrams and bigrams, fed into a Logistic Regression classifier with balanced class weights.

### Methodology & Training Source
Because `amazon_train_pool.csv` does not contain human-annotated intent labels, we could not train a supervised classifier natively. 
**Crucial Distinction**: We explicitly used a **Weakly-Supervised** labeling procedure. We sampled 20,000 examples from the completely isolated training pool and automatically assigned "weak labels" using the exact same rule-based heuristic regex pipeline previously validated during dataset exploration. 
**These weak labels are NOT ground truth**, but they provide a sufficient proxy signal to train the Logistic Regression baseline without leaking or spending resources on human annotation of the entire training pool.

### Input Variants
We evaluated two input variants to test the effect of conversational context:
*   **Variant A (Text Only)**: `customer_text`
*   **Variant B (Text + Context)**: `customer_text` + `previous_context`

### Evaluation Metrics
Evaluated strictly against the fully held-out 200-example `amazon_eval.csv` Golden Set.

**Variant A (Text Only)**
*   **Accuracy**: 89.50%
*   **Macro F1**: 0.8962
*   **Weighted F1**: 0.8948

**Variant B (Text + Context)**
*   **Accuracy**: 86.00%
*   **Macro F1**: 0.8634
*   **Weighted F1**: 0.8603

### Comparison & Limitations
*   **Massive Improvement**: The TF-IDF model crushes the majority baseline (89.5% vs 12.5% accuracy), proving that the text features carry immense predictive power for the taxonomy.
*   **Context Degradation**: Surprisingly, Variant A (Text Only) outperformed Variant B (Text + Context) by 3.5% in accuracy. Including `previous_context` in a simple bag-of-words TF-IDF model seems to introduce noise (irrelevant words from the agent's prior message) rather than resolving semantic ambiguity. This highlights the limitation of TF-IDF: it lacks the attention mechanisms needed to understand *how* the context relates to the current message.
*   **Weak Labels Limitation**: The model is fundamentally limited by the heuristics used to weak-label its training set. It essentially learned to mimic the regex rules, albeit smoothed over by ML. The 89.5% performance against the heuristic-based Golden Set is partly a reflection of the fact that the Golden Set itself was labeled using similar heuristics. A true manual evaluation is required for the production model.
