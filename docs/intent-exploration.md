# AmazonHelp Intent Exploration

## Overview
This document presents an exploratory analysis of customer inquiries directed at **AmazonHelp**, the primary candidate brand for the AI customer-support-agent assignment. 

The purpose of this analysis is to transparently identify recurring customer-support problem themes using frequency analysis and manual inspection, without prematurely imposing a final taxonomy.

## Identified Themes & Frequencies

Based on n-gram frequencies (unigrams/bigrams) and keyword matching over the corpus of inbound AmazonHelp messages, we've identified the following major thematic clusters. 

*(Note: A single message may overlap into multiple themes.)*

### 1. Delivery & Shipping
- **Approximate Frequency:** ~24,000+ examples
- **Common Keywords/Phrases:** `delivery`, `shipping`, `shipped`, `arrive`, `package`, `day delivery`, `next day`, `delivery date`, `amzl us` (Amazon Logistics)
- **Representative Examples:**
  - *"Ordered an item with guaranteed next day delivery. It still hasn't arrived. Tracking says delayed."*
  - *"My package was marked as delivered today but there is nothing on my porch."*
- **Classification Difficulty:** Generally easy to classify. Strong vocabulary signals (`tracking`, `arrived`, `delivered`).
- **Overlaps:** Often overlaps with Prime (e.g., "I pay for Prime but didn't get 2-day shipping").

### 2. Prime & Subscriptions
- **Approximate Frequency:** ~16,900+ examples
- **Common Keywords/Phrases:** `prime`, `subscription`, `membership`, `amazon prime`, `prime member`, `pay prime`
- **Representative Examples:**
  - *"Why was I charged $99 for Amazon Prime? I never signed up for it."*
  - *"I want to cancel my Prime membership and get a refund."*
- **Classification Difficulty:** Easy. The word "Prime" or "membership" strongly indicates this category.
- **Overlaps:** Heavy overlap with Refunds (users wanting refunds for accidental subscriptions) and Delivery (Prime shipping benefits).

### 3. Refunds & Returns
- **Approximate Frequency:** ~10,700+ examples
- **Common Keywords/Phrases:** `refund`, `return`, `returned`, `money back`, `charge`, `credit card`, `gift card`
- **Representative Examples:**
  - *"I returned an item 2 weeks ago and still haven't received my refund on my credit card."*
  - *"How do I return a defective product I bought last week?"*
- **Classification Difficulty:** Moderate to Easy. 
- **Overlaps:** Overlaps with Prime (refund for subscription) and Damaged/Missing items.

### 4. Damaged or Missing Items
- **Approximate Frequency:** ~2,700+ examples
- **Common Keywords/Phrases:** `damaged`, `missing`, `broken`, `empty`, `stolen`
- **Representative Examples:**
  - *"My box arrived completely crushed and the item inside is broken."*
  - *"I opened my package and it was completely empty. Someone stole the phone."*
- **Classification Difficulty:** Moderate. Requires differentiating between a late delivery and a delivery that arrived but was damaged/empty.

### 5. General Customer Service Complaints (Noise/Ambiguous)
- **Approximate Frequency:** ~13,300+ examples
- **Common Keywords/Phrases:** `customer service`, `support`, `chat`, `call`, `customer care`, `every time`, `don know`
- **Representative Examples:**
  - *"Your customer service is terrible, I've been on hold for 20 minutes."*
  - *"I keep getting transferred from one rep to another without an answer."*
- **Classification Difficulty:** Difficult. These are often meta-complaints about the support process itself rather than the core issue, making them highly ambiguous.

---

## Evaluation of Suitability for Assignment

**1. Does AmazonHelp contain enough customer-support diversity for a useful intent classifier?**
Yes. The dataset reveals distinct, real-world e-commerce categories such as delivery delays, subscription management (Prime), returns/refund processing, and damaged goods.

**2. Are there enough examples to create a 150–250 example manually labelled golden evaluation set?**
Absolutely. With over 154,000 inbound customer messages that received a brand reply, it is trivial to extract a high-quality, diverse, stratified sample of 150–250 items for a golden evaluation set.

**3. Which themes appear strongest?**
"Delivery & Shipping" and "Prime & Subscriptions" are the strongest, most distinct themes. They have high volume and distinct vocabularies. "Refunds & Returns" is also very strong.

**4. Which themes are difficult or ambiguous?**
"General Customer Service Complaints" are highly ambiguous. Customers ranting about wait times or unhelpful agents often omit the actual problem they are facing, making intent classification nearly impossible without prior conversation context. Furthermore, AmazonHelp handles a massive volume of multilingual queries (Spanish, French, Japanese, etc.), which adds noise if the classifier is expected to be English-only.

**5. Which themes could potentially be excluded from AUTO_HANDLE and instead routed to ESCALATE?**
- **Damaged or Missing Items:** Often requires human empathy, photo verification, or loss investigation.
- **Refunds & Returns (High Value/Exceptions):** Standard returns could be auto-handled, but disputes over missing refunds usually require agent intervention.
- **Ambiguous Complaints:** Any message solely expressing frustration without a clear entity (order/item) should be routed to a human.

**6. What initial observations should influence the future intent taxonomy?**
- The taxonomy should definitely include classes like `Delivery_Status`, `Prime_Management`, and `Return_Refund`.
- We need an `Escalate` or `Other` class to handle rants and meta-complaints.
- Given the multilingual nature of the AmazonHelp dataset (`de`, `que`, `la`, `en`, `un` are in the top unigrams), we either need to filter the dataset to English only before building the golden set, or ensure the classifier supports multiple languages. filtering to English is highly recommended for the SDE intern scope.
