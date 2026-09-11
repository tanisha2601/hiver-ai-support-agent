# Evaluation Split Strategy & Leakage Protection

This document details the strategy for dividing the filtered `AmazonHelp` TWCS dataset into Training, Development (Validation), and Golden Evaluation sets.

## 1. The Danger of Conversation Leakage

In standard machine learning classification tasks, data is often split randomly by row (e.g., an 80/10/10 random split). For the TWCS dataset, performing a simple row-wise random split will cause severe **Data Leakage**.

**Why?**
The TWCS dataset consists of multi-turn conversational threads. 
If a customer sends three tweets in a row explaining a complex missing package issue:
- Tweet 1: *"Where is my package?"*
- Tweet 2: *"Tracking says it arrived but it isn't here."*
- Tweet 3: *"I've checked the porch and with neighbors."*

If we randomly split by row, Tweet 1 and Tweet 3 might end up in the **Training Set**, while Tweet 2 ends up in the **Evaluation Set**. 
The model will "memorize" the vocabulary, entities, and context of this specific user's problem during training, giving it an unfair and unrealistic advantage when classifying Tweet 2 during evaluation. It will not be evaluating generalizable intent classification.

## 2. Conversation-Level Splitting

To prevent leakage, all dataset splitting must be performed at the **Conversation Level**, using the reconstructed `conversation_id` (the `root_tweet_id` of the conversational tree).

**Rule**: All tweets belonging to the same conversation thread must be grouped together and assigned entirely to a single split (Train, Dev, OR Test). They must never straddle the boundaries.

## 3. Golden Set Isolation & Leakage Prevention

We extracted exactly **200 candidate examples** to serve as the **Golden Evaluation Set**. 
*Note: This dataset is AI-assisted. It was explicitly stratified and labeled by heuristic scripts rather than manually annotated by humans.*

To ensure the Golden Set remains completely unseen and untouched by any future model training or baseline development, we performed a strict exclusion filter:
1. Every candidate in `amazon_eval.csv` (the golden set) has an associated `conversation_id`.
2. We extracted the set of all unique `conversation_id`s present in the Golden Set (199 unique conversations).
3. We filtered the remaining bulk dataset (`amazon_english_inbound.csv`) to drop **all** rows matching these Golden `conversation_id`s.

This guarantees zero crossover. A conversation appearing in the Golden Evaluation Set will never appear in the Training data in any form.

## 4. Current Split Metrics
- **Total Golden Examples**: 200
- **Unique Golden Conversations**: 199
- **Total Amazon Messages (Before Exclusion)**: 179,372
- **Total Amazon Messages (After Exclusion)**: 178,245
- **Excluded Messages**: 1,127
- **Excluded Conversations**: 199
- **Leakage Check**: PASS (0 overlapping conversations between the training pool and evaluation set)
