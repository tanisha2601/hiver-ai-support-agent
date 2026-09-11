# Retrieval System

## 1. Retrieval Architecture
The retrieval component uses a classic TF-IDF (Term Frequency-Inverse Document Frequency) approach with Cosine Similarity. When a new customer query arrives, it is vectorized into the pre-computed TF-IDF vector space, and the system performs a k-Nearest Neighbors search using cosine distance to retrieve the most semantically similar historical customer inquiries.

## 2. Why Historical Conversations are Used
Instead of answering every query from scratch or using static knowledge base articles, we leverage the vast TWCS historical corpus. By retrieving a historical conversation where a customer asked a similar question, we implicitly retrieve the *actual, real-world brand response* provided by a human AmazonHelp agent. This allows the eventual LLM to mimic the brand's tone, policy, and exact resolution steps.

## 3. TF-IDF Representation
We vectorize customer texts using:
- Word unigrams and bigrams (`ngram_range=(1, 2)`)
- Lowercasing
- English stop-words removal
- `min_df=3` (ignoring typos and extreme rarities)
- L2 Normalization (ensuring length-agnostic cosine similarity)
- `max_features=50,000` (for memory efficiency)

## 4. Cosine Similarity
Cosine similarity is measured between the normalized L2 vectors of the incoming query and all 134,821 valid historical customer messages.

## 5. K Values Tested
We retrieve and evaluate the top K=5 results, analyzing metrics at `K=1`, `K=3`, and `K=5`.

## 6. Leakage Prevention
**Zero Intersection Guarantee:** The 199 unique conversations present in the Golden Evaluation Set were strictly excluded from the TF-IDF corpus before index building. We mathematically guarantee that a query cannot retrieve its own historical response, nor any response from the same conversational thread.

## 7. Retrieval Metrics
Evaluated on the 200 Golden Set queries:
*   **Intent Match @1**: 43.50%
*   **Intent Match @3**: 60.00%
*   **Intent Match @5**: 73.00%
*   **Average Similarity**: 0.4095
*   **Median Similarity**: 0.3565

## 8. Limitations of Intent-Match Proxy Evaluation
Because we do not have human-annotated relevance judgments for the 134k historical pairs, we cannot compute true Recall or NDCG. Instead, we use an **Intent-Match Proxy**: we assume a retrieved example is "relevant" if its weak-labeled intent matches the Golden Query's true intent. This is a highly imperfect proxy. A retrieved query might be in the same intent bucket (e.g., `DELIVERY_SHIPPING`) but relate to a completely different sub-issue (e.g., "lost package" vs "tracking link broken").

## 9. Why Similarity Alone Does Not Guarantee a Good Support Response
TF-IDF identifies lexical overlap. A query like *"My package is late, please help"* might retrieve *"My package is early, please help"* with a very high similarity score. However, the human agent's response to an early package is entirely useless for resolving a late package. This is why retrieval is only the first step; an LLM is required to synthesize and adapt the retrieved knowledge.
