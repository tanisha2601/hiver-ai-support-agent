# Dataset Analysis: Customer Support on Twitter (TWCS)

## 1. Dataset Overview

The **Customer Support on Twitter (TWCS)** dataset is a large-scale corpus of modern customer support interactions on Twitter between consumers and major corporate customer support accounts.

This document records the verified dataset statistics and structural analysis performed during Step 2 and Step 3.

---

## 2. Dataset Dimensions & Storage

| Metric | Verified Value |
| :--- | :--- |
| **Source File** | `data/raw/twcs.csv` |
| **Total Records (Rows)** | `2,811,774` |
| **Total Features (Columns)** | `7` |
| **In-Memory Size (Pandas)** | `557.84 MB` |
| **Duplicate Rows** | `0 (0.00%)` |
| **Total Unique Authors** | `702,777` |
| **Total Inbound (Customer) Messages** | `1,537,843 (54.69%)` |
| **Total Outbound (Brand) Messages** | `1,273,931 (45.31%)` |
| **Overall Dataset Date Range** | `2008-05-08 20:13:59+00:00` to `2017-12-03 23:14:01+00:00` |
| **Reconstructed Conversation Trees** | `798,197` |

---

## 3. Schema & Data Types

| Column Name | Inferred Dtype | Logical Description |
| :--- | :--- | :--- |
| `tweet_id` | `int64` | Unique numeric identifier for the tweet |
| `author_id` | `string` | Anonymized user ID (e.g. `115712`) for customers, or public handle (e.g. `AppleSupport`) for brands |
| `inbound` | `boolean` | `True` for customer messages directed to brands; `False` for brand responses |
| `created_at` | `string` (datetime) | Twitter formatted timestamp string (`%a %b %d %H:%M:%S %z %Y`) |
| `text` | `string` | UTF-8 text content of the tweet, including emojis and masked entity tokens |
| `response_tweet_id` | `string` | Comma-separated tweet IDs that responded to this tweet (or `NaN` if leaf/unanswered) |
| `in_response_to_tweet_id` | `float64` | Parent tweet ID to which this tweet responds (or `NaN` if root) |

---

## 4. Missing Values Analysis

| Column | Missing Count | Missing Percentage | Data Interpretation |
| :--- | :---: | :---: | :--- |
| `tweet_id` | 0 | 0.00% | Primary key; fully populated |
| `author_id` | 0 | 0.00% | Fully populated |
| `inbound` | 0 | 0.00% | Fully populated boolean |
| `created_at` | 0 | 0.00% | Fully populated timestamp |
| `text` | 0 | 0.00% | Fully populated message body |
| `in_response_to_tweet_id` | 794,335 | 28.25% | Expected: indicates the message is the **root/origin** of a conversation thread |
| `response_tweet_id` | 1,040,629 | 37.01% | Expected: indicates the message is a **leaf node** (received no further replies in dataset) |

---

## 5. Conversation Graph & Relational Structure

1. **Parent-Child Linkage**:
   - `in_response_to_tweet_id` points to the immediate predecessor tweet in the conversation thread.
   - Out of 2,811,774 total messages, **2,013,577 records** have valid parent links resolving to another tweet in the dataset.
   - Tracing parent pointers upward partitions the dataset into **798,197 distinct conversation trees**.

2. **Top Customer Support Accounts by Volume**:
   - `AmazonHelp`: 169,840 brand messages
   - `AppleSupport`: 106,860 brand messages
   - `Uber_Support`: 56,270 brand messages
   - `SpotifyCares`: 43,265 brand messages
   - `Delta`: 42,253 brand messages

---

## 6. Data Quality Observations

### Verified Facts:
- **No Duplicate Records**: Every row has a unique `tweet_id`.
- **Zero Empty Text Fields**: Every tweet contains non-empty text (though length and cleanliness vary).
- **Reciprocal Reply Relationships**: For tweets with in-dataset parents, `in_response_to_tweet_id` accurately matches the parent's `tweet_id` and is indexed in the parent's `response_tweet_id` field.
- **Entity Masking**: Sensitive customer data (emails, credit card numbers, phone numbers, order IDs) was masked by the dataset creators with tokens such as `__email__`, `__number__`, `__credit_card__`.

### Structural Interpretations:
- **Root Nodes**: Messages with `in_response_to_tweet_id == NaN` represent the beginning of conversation threads or self-contained broadcasts.
- **Multi-Part Tweets**: Customers frequently post numbered follow-up tweets (`1/2`, `2/2`) when explaining complex issues. These appear as child nodes linked via `in_response_to_tweet_id`.
- **External Image References**: Inquiries referencing screenshots or images require textual understanding, as binary image attachments are not present in Twitter CSV exports.
