# Data Filtering Strategy (AmazonHelp)

This document outlines the deterministic, reproducible pipeline used to filter the raw TWCS dataset down to a clean, English-language subset for intent classification of `AmazonHelp` customer queries.

## 1. Brand Selection Rule
We isolate only the conversation trees where `AmazonHelp` participated. 
- We identify all tweets where `author_id == 'AmazonHelp'`.
- Using parent-child linkages (`in_response_to_tweet_id`), we trace back to the root of the conversation.
- We extract all tweets (both customer and brand) belonging to these specific conversation roots.

## 2. Inbound / Customer Selection Rule
For intent classification, we only care about what the *customer* is saying.
- We filter the conversation dataset down to rows where `inbound == True`.
- We preserve the `in_response_to_tweet_id` pointer so we can later extract the previous message (which might be a brand message) for context.

## 3. Handling Missing / Invalid Text
- We remove any rows where `text` is null or NaN.
- We strip leading/trailing whitespace.
- We remove rows where the cleaned text length is less than 5 characters (e.g., just an emoji or a single "?").

## 4. English Language Filtering Approach
As requested, we do NOT rely on an LLM for language detection. We also must use a transparent and reproducible strategy.
- We use the `langdetect` Python library (a port of Google's language-detection library), which uses Naive Bayes character n-gram models.
- If `langdetect` throws an exception (e.g., if the text contains no letters), we drop the row.
- We only keep rows where `detect(text) == 'en'`.

## 5. Handling of Duplicates
- The original TWCS dataset contains exactly 0 duplicate `tweet_id`s.
- However, we also deduplicate exact text matches *from the same author* to prevent spam bursts from leaking across training and evaluation sets.
- If a customer sends the exact same text multiple times, we keep only the first instance (sorted chronologically).

## 6. Handling of Ambiguous / Noisy Messages
- We do not programmatically remove ambiguous messages. Noisy messages, rants, and vague follow-ups are an authentic part of social media support.
- These will be handled downstream during manual annotation (via the `OTHER` or `CUSTOMER_SERVICE_COMPLAINT` labels) and subsequent model training.

## 7. Approximate Data Funnel Statistics

*Note: These statistics are generated dynamically by the `prepare_amazon_data.py` script.*
- **Raw TWCS Dataset**: 2,811,774 tweets
- **AmazonHelp Conversations (All Tweets)**: 374,042 tweets
- **AmazonHelp Inbound Messages**: 203,598 tweets
- **After Text Cleaning & Deduplication**: 203,351 tweets
- **After English Filtering**: 179,372 tweets (final cleaned dataset for candidate generation)
