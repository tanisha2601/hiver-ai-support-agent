# Golden Set Labeling Guidelines

This document establishes the precise manual annotation rules for evaluating the Customer Support AI Agent's intent classification performance. The goal is to build a robust, historically accurate, and realistic "Golden Set" of 150-250 examples.

## Core Annotation Philosophy
**Replicate the agent's real-time state.** You must annotate the message based *only* on the knowledge the agent would have had at the exact moment the tweet was received. Do not peek at future messages to resolve ambiguity if the current message is fundamentally unclear.

---

## 1. Identifying the Primary Intent
Read the `customer_text`. Ask yourself: *What is the primary action this customer wants the support agent to take?* Map this action to one of the 10 approved intents in the taxonomy (e.g., `DELIVERY_SHIPPING`, `REFUND_RETURN`).

## 2. Handling Multiple Issues (Choosing the Dominant Intent)
Customers frequently list multiple grievances in a single tweet (e.g., "My package is late, and when it finally arrived the box was empty, plus your customer service is terrible!").
* **Rule**: Choose the most *actionable* and *severe* intent.
* **Hierarchy**: `DAMAGED_MISSING_ITEM` > `ACCOUNT_LOGIN` > `PAYMENT_BILLING` > `ORDER_MODIFICATION` > `REFUND_RETURN` > `DELIVERY_SHIPPING` > `PRIME_SUBSCRIPTION` > `CUSTOMER_SERVICE_COMPLAINT`.
* *Example*: The tweet above should be labeled `DAMAGED_MISSING_ITEM` because an empty box is the critical blocker requiring escalation.

## 3. Handling Vague Complaints
If a customer complains without specifying the core issue (e.g., "I am so mad at Amazon right now, I'm never shopping here again!"), look at the context. 
* If there is no previous context explaining why, label it as `CUSTOMER_SERVICE_COMPLAINT` (if directed at the brand's support/service) or `OTHER` (if it's a general rant). Do not guess the underlying order issue.

## 4. Insufficient Context & Follow-up Messages
Many messages in Twitter threads are highly contextual: "Yes", "Still waiting", "I already did that", "Order #12345".
* **Rule**: Do not assign an intent merely because a message is a follow-up. Instead, use the previous conversation context to determine the underlying semantic intent whenever possible.
* **Fallback**: If the underlying intent still cannot be determined reliably even with previous context, assign `OTHER`.
* **Note**: Set the `needs_context` flag to `True` for these rows in the dataset. Keep the concepts of `intent` and `needs_context` completely separate.

## 5. Using Conversation Context (Examples)
If a message is a follow-up, use the `previous_context` field to understand what the customer is replying to.

**Example 1**
Customer: "Where is my package?"
Intent: `DELIVERY_SHIPPING`
needs_context: false

**Example 2**
Customer: "Still waiting."
Previous context: "My package was supposed to arrive yesterday."
Intent: `DELIVERY_SHIPPING`
needs_context: true

**Example 3**
Customer: "Yes."
Previous context: "Would you like help with your refund?"
Intent: `REFUND_RETURN`
needs_context: true

**Example 4**
Customer: "I already did that."
Previous context is insufficient to determine the issue.
Intent: `OTHER`
needs_context: true

## 6. Multilingual / Non-English Messages
Our AI agent is currently scoped to English.
* **Rule**: If a message is primarily in a language other than English (e.g., Spanish, French, Hindi), label it as `OTHER`. Add a note in `annotation_notes` (e.g., "Spanish").

## 7. Spam and Noise
Tweets containing unrelated affiliate links, random mentions, jokes, or automated bot spam should be immediately labeled as `OTHER`.

## 8. Handling Ambiguous Examples
If an example truly sits perfectly between two intents and the tie-breaking rules do not help, or if the text is completely incomprehensible:
* Select `OTHER`.
* Set the `difficulty` field to `High`.
* Document the confusion in `annotation_notes`. 

## 9. Assigning OTHER
Use `OTHER` for:
1. Spam/Noise
2. Non-English queries
3. Incomprehensible text
4. Chit-chat / Compliments ("Thanks!", "Amazon is the best")
5. True edge cases that don't fit the 8 core taxonomy buckets.

## 10. Avoiding Future Knowledge
**CRITICAL**: Do not use information from subsequent tweets in the thread to classify the current tweet. 
* *Example*: Tweet A says "I need help." (Label: `CUSTOMER_SERVICE_COMPLAINT` or `OTHER`). Tweet B says "My TV is broken." If you are annotating Tweet A, you must ignore your knowledge of Tweet B. The agent would not have known about the TV when it received Tweet A. Label Tweet A based strictly on what is written in Tweet A (and any prior context).
