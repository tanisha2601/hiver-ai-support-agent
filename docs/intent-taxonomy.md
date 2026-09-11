# Final Intent Taxonomy (AmazonHelp)

Based on the exploratory analysis of the AmazonHelp TWCS dataset, we have defined a practical, mutually exclusive, and comprehensively covering intent taxonomy for the Customer Support AI Agent.

This taxonomy is designed to be easily understandable by SDE interns, useful for automated routing, and robust enough for realistic e-commerce support queries.

## 1. DELIVERY_SHIPPING
* **Definition**: Inquiries related to the status, tracking, delay, or delivery process of an order that has already been placed but not yet successfully received.
* **Belongs Here**: "Where is my package?", "Tracking says delivered but I don't have it", "My guaranteed next day delivery is late", questions about Amazon Logistics / AMZL.
* **Does NOT Belong**: "My package arrived but it's empty" (-> `DAMAGED_MISSING_ITEM`), "I want to cancel my order before it ships" (-> `ORDER_MODIFICATION`).
* **Positive Examples**: 
  - *"Ordered an item with guaranteed next day delivery. It still hasn't arrived."*
  - *"Can you tell me why my package tracking hasn't updated in 3 days?"*
* **Closest Confusing Intent**: `DAMAGED_MISSING_ITEM`. 
* **Tie-Breaking Rule**: If the customer never physically received the box, it's `DELIVERY_SHIPPING`. If they received the box but the item inside is missing/stolen, it's `DAMAGED_MISSING_ITEM`.
* **Safe for AUTO_HANDLE?**: Yes. Tracking status can usually be looked up automatically.
* **Escalate?**: No.
* **Reason for Inclusion**: The highest volume issue in the Amazon dataset (~24,000+ keywords).

## 2. PRIME_SUBSCRIPTION
* **Definition**: Questions or issues relating to Amazon Prime memberships, digital subscriptions (Kindle Unlimited, Audible), renewals, or cancellation of subscriptions.
* **Belongs Here**: "Cancel my Prime", "Why was I charged $119 for Prime?", "Do I get Prime video with this?"
* **Does NOT Belong**: "My Prime package is late" (-> `DELIVERY_SHIPPING`).
* **Positive Examples**: 
  - *"I want to cancel my Prime membership and get a refund."*
  - *"How do I share my Prime benefits with my wife?"*
* **Closest Confusing Intent**: `PAYMENT_BILLING` (for unexpected Prime charges) or `REFUND_RETURN` (asking for Prime refund).
* **Tie-Breaking Rule**: If the core entity being discussed is a "Prime" membership or subscription, classify as `PRIME_SUBSCRIPTION` regardless of whether they want a refund for it.
* **Safe for AUTO_HANDLE?**: Yes. Canceling or explaining Prime benefits is highly automatable.
* **Escalate?**: No.
* **Reason for Inclusion**: Distinct, high-volume topic with a clear automated resolution pathway.

## 3. REFUND_RETURN
* **Definition**: Requests to return a purchased physical item or inquiries about the status of a refund for a returned/cancelled item.
* **Belongs Here**: "How do I return this?", "I returned my shoes 2 weeks ago, where is my refund?", "Can I get my money back?"
* **Does NOT Belong**: "I want a refund for my Prime membership" (-> `PRIME_SUBSCRIPTION`).
* **Positive Examples**: 
  - *"I dropped off my return at UPS yesterday. When will my credit card be refunded?"*
  - *"The dress doesn't fit, how do I print a return label?"*
* **Closest Confusing Intent**: `PAYMENT_BILLING` or `ORDER_MODIFICATION`.
* **Tie-Breaking Rule**: If the customer is returning an item they received, or waiting for money back from a return/cancellation, it's `REFUND_RETURN`.
* **Safe for AUTO_HANDLE?**: Yes, generating return labels and checking refund status is automatable.
* **Escalate?**: No, unless the refund is significantly delayed.
* **Reason for Inclusion**: A core e-commerce function with distinct vocabulary.

## 4. DAMAGED_MISSING_ITEM
* **Definition**: The customer physically received their delivery package, but the item inside is damaged, defective, completely missing, or the wrong item was sent.
* **Belongs Here**: "My TV screen is cracked", "The box was completely empty", "I ordered a book and got a DVD".
* **Does NOT Belong**: "My package never arrived" (-> `DELIVERY_SHIPPING`).
* **Positive Examples**: 
  - *"My box arrived completely crushed and the item inside is broken."*
  - *"I opened my package and it was completely empty. Someone stole the phone."*
* **Closest Confusing Intent**: `DELIVERY_SHIPPING` or `REFUND_RETURN`.
* **Tie-Breaking Rule**: If the package arrived but the *contents* are the problem, it is `DAMAGED_MISSING_ITEM`. If the customer asks to return a damaged item, tag as `DAMAGED_MISSING_ITEM` (the root cause takes precedence over the resulting return request).
* **Safe for AUTO_HANDLE?**: No.
* **Escalate?**: Yes. Fraud, missing items, or damaged goods often require human empathy, photo verification, or loss investigation.
* **Reason for Inclusion**: A high-severity issue that requires specific escalation handling.

## 5. PAYMENT_BILLING
* **Definition**: Issues regarding payment methods, declined cards, gift card balances, or unexpected charges (unrelated to Prime).
* **Belongs Here**: "My credit card was charged twice", "Gift card code isn't working", "Why did my payment decline?"
* **Does NOT Belong**: "Where is my refund?" (-> `REFUND_RETURN`).
* **Positive Examples**: 
  - *"I tried to buy a book but Amazon says my payment method needs to be updated."*
  - *"I bought a $50 gift card but the balance says $0."*
* **Closest Confusing Intent**: `PRIME_SUBSCRIPTION` or `REFUND_RETURN`.
* **Tie-Breaking Rule**: If it's an unexpected charge for Prime, use `PRIME_SUBSCRIPTION`. Otherwise, payment failures and gift card issues are `PAYMENT_BILLING`.
* **Safe for AUTO_HANDLE?**: Partially. 
* **Escalate?**: Yes, if there is a suspected double-charge or fraud.
* **Reason for Inclusion**: Payment issues are critical blockers for e-commerce and require different backend API checks than shipping.

## 6. ACCOUNT_LOGIN
* **Definition**: Problems accessing the Amazon account, password resets, locked accounts, or security concerns.
* **Belongs Here**: "I forgot my password", "My account is locked for suspicious activity", "How do I change my email?"
* **Does NOT Belong**: "How do I change my shipping address on an order?" (-> `ORDER_MODIFICATION`).
* **Positive Examples**: 
  - *"I am locked out of my account and not receiving the OTP SMS."*
  - *"Someone hacked my Amazon account and changed the password."*
* **Closest Confusing Intent**: `PAYMENT_BILLING` (if fraud occurred).
* **Tie-Breaking Rule**: If the primary issue is gaining access to the account, it's `ACCOUNT_LOGIN`.
* **Safe for AUTO_HANDLE?**: Partially (password reset links).
* **Escalate?**: Yes, if account takeover is suspected.
* **Reason for Inclusion**: High-security queries require strict verification protocols.

## 7. ORDER_MODIFICATION
* **Definition**: Requests to change an active order before it has been shipped or delivered.
* **Belongs Here**: "Cancel my order", "Change my shipping address", "Change the color of the shirt I just bought".
* **Does NOT Belong**: "Cancel my Prime" (-> `PRIME_SUBSCRIPTION`).
* **Positive Examples**: 
  - *"I accidentally ordered two of these, how do I cancel one?"*
  - *"Can I update the delivery address on order #123 before it ships?"*
* **Closest Confusing Intent**: `REFUND_RETURN` (if order is already shipped).
* **Tie-Breaking Rule**: If the item hasn't shipped/arrived yet, it's `ORDER_MODIFICATION`. If it has arrived, it's a `REFUND_RETURN`.
* **Safe for AUTO_HANDLE?**: Yes.
* **Escalate?**: No.
* **Reason for Inclusion**: Pre-shipment modifications are a standard automated workflow.

## 8. CUSTOMER_SERVICE_COMPLAINT
* **Definition**: Meta-complaints about the support process itself, wait times, rude agents, or frustration, where the actual underlying order issue is omitted or secondary.
* **Belongs Here**: "I've been on hold for 2 hours", "Your customer rep was incredibly rude", "Why can't I talk to a human?"
* **Does NOT Belong**: Frustrated complaints that clearly state the problem: "I'm so angry my package is late!" (-> `DELIVERY_SHIPPING`).
* **Positive Examples**: 
  - *"Your customer service is terrible, I've been transferred 4 times."*
  - *"Why is it so impossible to find a phone number to call you guys?"*
* **Closest Confusing Intent**: `OTHER`.
* **Tie-Breaking Rule**: If the tweet is specifically complaining about the *service/support experience*, it belongs here. 
* **Safe for AUTO_HANDLE?**: No.
* **Escalate?**: Yes. The user is highly agitated; an automated response will likely worsen the situation.
* **Reason for Inclusion**: Very high frequency in TWCS; requires immediate de-escalation by human agents.

## 9. OTHER
* **Definition**: Spam, off-topic messages, non-support-related chit-chat, or inquiries that do not fit into any of the above categories.
* **Belongs Here**: "Amazon is taking over the world", "I love my new Kindle!", spam links, ambiguous text.
* **Positive Examples**: 
  - *"Shoutout to Amazon for having the best book selection."*
  - *"Check out my new affiliate link for Amazon deals!"*
* **Closest Confusing Intent**: `CUSTOMER_SERVICE_COMPLAINT`.
* **Tie-Breaking Rule**: If it's not a complaint and not a support request, it's `OTHER`.
* **Safe for AUTO_HANDLE?**: Yes (can be safely ignored or given a generic "Thanks!" reply).
* **Escalate?**: No.
* **Reason for Inclusion**: Essential fallback bucket for realistic, noisy social media streams.
