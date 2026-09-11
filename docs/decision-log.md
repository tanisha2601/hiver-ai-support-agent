# Engineering Decision Log

## 1. Selected Corpus: AmazonHelp Twitter Dataset
**Decision**: Use the AmazonHelp subset of the Customer Support on Twitter dataset.
**Reason**: Provides a large, realistic, and diverse set of customer support interactions from a well-known brand, making it ideal for retrieval and generation.
**Trade-off**: The dataset is public and potentially noisy, requiring preprocessing and dealing with generic responses (e.g., "DM us").
**Impact**: Established a realistic foundation for the agent's behavior and tone.

## 2. Nine Explicit Intents Selected
**Decision**: Restrict intent classification to 9 specific categories (e.g., DELIVERY_SHIPPING, ACCOUNT_LOGIN, etc.).
**Reason**: Simplifies the classification task and maps directly to distinct support actions/policies.
**Trade-off**: May not cover edge cases or rare issues effectively.
**Impact**: Provided a clear framework for the classifier and escalation rules.

## 3. Separated Context from Intent
**Decision**: Classify intent independently of previous context but use context for retrieval and generation.
**Reason**: Prevents the intent classifier from being overly influenced by generic follow-up text.
**Trade-off**: May miss nuanced intents that are only clear when reading the full conversation.
**Impact**: Improved modularity and intent accuracy.

## 4. Evaluation Conversations Blacklisted
**Decision**: Strictly blacklist the conversation IDs in the evaluation set from the retrieval corpus.
**Reason**: Prevents data leakage where the agent could retrieve the exact subsequent response from the same conversation.
**Trade-off**: Reduces the size of the retrieval pool slightly.
**Impact**: Ensures evaluation metrics reflect true generalization.

## 5. Retained TF-IDF Baseline
**Decision**: Retain the TF-IDF retrieval system as a fallback.
**Reason**: Provides a deterministic, lightweight, and fast fallback when semantic models fail to load or are unavailable.
**Trade-off**: Adds complexity to the retrieval layer.
**Impact**: Ensures the system can run entirely offline on low-resource hardware.

## 6. Added Semantic Retrieval
**Decision**: Integrated `sentence-transformers` (`all-MiniLM-L6-v2`) for semantic retrieval.
**Reason**: Captures semantic meaning beyond exact keyword matches, improving retrieval quality for paraphrased queries.
**Trade-off**: Increases model size and computational overhead.
**Impact**: Significantly improves the relevance of retrieved historical examples.

## 7. Selected Hybrid Retrieval (alpha=0.7)
**Decision**: Combine TF-IDF and Semantic retrieval with a 0.7 weight towards semantic.
**Reason**: Leverages the strengths of both exact keyword matching (TF-IDF) and semantic understanding.
**Trade-off**: Requires running both retrievers and blending scores.
**Impact**: Provides the most robust retrieval performance.

## 8. Utilized Weak Supervision
**Decision**: Train the intent classifier using heuristically generated "weak" labels rather than manual annotations.
**Reason**: Scales training data massively without the cost of human annotation.
**Trade-off**: The classifier learns the heuristic biases and may inherit its flaws.
**Impact**: Accelerated development but necessitates transparent disclosure of methodology.

## 9. Disclosed AI-Assisted Labels
**Decision**: Explicitly label evaluation metrics as "AI-assisted stratified evaluation labels".
**Reason**: Maintains academic and engineering honesty; the metrics are proxies, not ground truth.
**Trade-off**: The reported accuracy may seem less definitive.
**Impact**: Prevents misleading claims about the system's human-level accuracy.

## 10. Conservative Escalation Policy
**Decision**: Escalate queries aggressively based on intent, confidence, and grounding.
**Reason**: In a customer service setting, hallucinating a wrong answer is far worse than routing to a human.
**Trade-off**: Increases the load on human agents (lower auto-handle rate).
**Impact**: Ensures high safety and reliability in production.

## 11. Emphasized Response Grounding
**Decision**: Require responses to be grounded in high-quality retrieved historical examples.
**Reason**: Prevents the LLM from inventing policies or hallucinating actions.
**Trade-off**: Responses may occasionally sound disjointed if retrieval is weak.
**Impact**: Dramatically increases factual accuracy and policy adherence.

## 12. Raw Data Not Committed
**Decision**: Keep raw datasets out of version control and cache them locally.
**Reason**: Datasets and embeddings are too large for Git and may have licensing restrictions.
**Trade-off**: Requires a setup step to download and place data.
**Impact**: Keeps the repository lightweight and clean.

## 13. LLM-as-Judge Labeled as Non-Human Evaluation
**Decision**: Explicitly document that reply quality metrics are LLM/heuristic proxies, not human-rated.
**Reason**: Transparency. LLM-as-judge has known biases.
**Trade-off**: Quality metrics are directional rather than absolute.
**Impact**: Sets correct expectations for stakeholders reviewing the metrics.
