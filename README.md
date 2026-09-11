# Hiver AI Support Agent

An evaluated, prototype AI customer-support agent for AmazonHelp that:
- classifies customer intents across a 9-category taxonomy
- retrieves historically similar support conversations for grounded evidence
- generates grounded, brand-aligned draft replies
- makes deterministic `AUTO_HANDLE` vs. `ESCALATE` routing decisions
- includes baseline benchmarks, an LLM-as-a-Judge evaluation engine, and failure analysis

---

## 1. Framing & Scope

This system is designed as an evaluated **prototype AI support agent** rather than an off-the-shelf production deployment. Its primary objective is to demonstrate rigorous evaluation methodology, conversational reconstruction, retrieval grounding, and safe policy escalation using real-world e-commerce support data.

The agent operates over four core stages:
1. **Intent Classification**: Identifies customer issue categories.
2. **Historical Resolution Retrieval**: Queries past resolved customer-support conversations as the source of factual precedent and policy evidence.
3. **Grounded Response Generation**: Drafts empathetic replies strictly rooted in retrieved evidence.
4. **Escalation Policy**: Safely routes ambiguous, sensitive, ungrounded, or complex queries to human staff.

### What I Did Not Build

To prioritize a runnable, transparently evaluated prototype within the scope of this assignment, several production-grade systems were intentionally omitted:
* **Real Account / Order APIs**: The agent has no access to live Amazon customer accounts or internal ordering databases.
* **Transaction Execution**: The agent cannot execute real cancellations, initiate card refunds, or alter delivery addresses.
* **Authentication & Authorization**: No user session management, OAuth, or customer verification mechanisms.
* **Production Ticketing & CRM Integration**: No live Zendesk/Hiver webhook dispatching or agent reassignment queues.
* **Enterprise Vector Infrastructure**: Relies on lightweight local TF-IDF and embedded MiniLM indices rather than managed distributed vector databases (e.g., Pinecone/Milvus).
* **Automated Tool Calling**: Actions are guided by policy responses rather than autonomous function calling.
* **Production Monitoring & SLA Infrastructure**: No distributed tracing, APM, or real-time latency budget managers.

---

## 2. Project Flow & Architecture

```text
Customer Message & Context
            ↓
┌──────────────────────────────────────┐
│       1. Intent Classification       │ → Predicts 1 of 9 intents & confidence
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│        2. Hybrid Retrieval           │ → Fetches past resolved support precedents
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│       3. Grounding Assessment        │ → Verifies factual support in retrieved examples
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│       4. Response Generation         │ → Drafts brand reply conditioned on evidence
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│        5. Escalation Policy          │ → AUTO_HANDLE vs. ESCALATE with explicit reason
└──────────────────────────────────────┘
```

---

## 3. Intent Taxonomy

The system defines 9 mutually exclusive semantic intents:

| Intent | Description | Boundary Rule |
| :--- | :--- | :--- |
| `DELIVERY_SHIPPING` | Tracking, delay, courier issues, estimated delivery dates. | Use when package transit is the primary issue. |
| `PRIME_SUBSCRIPTION` | Prime membership billing, auto-renewal, Prime Video streaming. | Specific to Amazon Prime services and benefits. |
| `REFUND_RETURN` | Return labels, drop-off locations, refund status. | Applies after item delivery or return initiation. |
| `DAMAGED_MISSING_ITEM` | Defective, broken, unsealed, missing parts, wrong item. | Physical item condition upon arrival. |
| `PAYMENT_BILLING` | Card charges, unknown transactions, invoice requests. | Monetary transactions and payment failures. |
| `ACCOUNT_LOGIN` | Password resets, OTP issues, 2FA, account lockouts. | Identity and authentication barriers. |
| `ORDER_MODIFICATION` | Address changes, order cancellation prior to dispatch. | Changes requested before shipment. |
| `CUSTOMER_SERVICE_COMPLAINT` | Grievances regarding agent conduct, long holds, disconnects. | Always hard-escalated to human teams. |
| `OTHER` | Off-topic remarks, casual banter, phishing reports, general inquiry. | Fallback when outside defined boundaries. |

---

## 4. Evaluation Methodology

To ensure transparent evaluation, the project distinguishes between three evaluation layers:

### A. Intent Evaluation
* **Evaluation Corpus**: A stratified 200-example evaluation set (`evaluation/golden_set.csv`) extracted from held-out conversation threads.
* **Provisional Nature**: Candidate labels were curated via **AI-assisted heuristic stratification** rather than fully independent human annotation.
* **Leakage-Free Partitioning**: Split strictly at the `conversation_id` level; evaluation conversations are permanently blacklisted from retrieval pools.

### B. Reply-Quality Evaluation
* **Real LLM-as-a-Judge**: Evaluates responses using a versioned prompt (`src/evaluation/prompts.py`) across five 1–5 rubric dimensions: *Relevance*, *Helpfulness*, *Groundedness*, *Clarity*, and *Unsupported Claims / Hallucination*.
* **Evidence-Conditioned**: The judge receives customer queries, conversation context, predicted intents, and retrieved precedents, strictly penalizing ungrounded promises.
* **Human Review Tooling**: A local GUI (`src/evaluation/reply_quality_reviewer.py`) and stratified 30-example sample (`evaluation/reply_quality_human_review.csv`) exist for human alignment studies.
* **Agreement Status**: Human-vs-LLM agreement metrics were **not measured** in this submission because the human review sample was not manually completed.

### C. Retrieval Evaluation
* **Proxy Metric**: Retrieval effectiveness is measured via intent-match agreement between the query and retrieved historical examples. This is an automated proxy and not a substitute for human relevance judgments.

---

## 5. Evaluation Results

Evaluated against the held-out 200-example evaluation set:

| Model | Accuracy | Macro F1 | Weighted F1 | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Majority Baseline** | 12.5% | 2.5% | 2.8% | Always predicts `DELIVERY_SHIPPING` (dominant class floor). |
| **TF-IDF + LogReg (Text + Context)** | 86.0% | 86.3% | 86.0% | Classical ML trained on weakly supervised training pool. |
| **Final Agent Pipeline** | 85.5% | 86.0% | 85.6% | Hybrid pipeline with rule-based safety escalation. |

*Note*: The Text-Only variant of TF-IDF + Logistic Regression achieved 89.5% accuracy. Both baseline and agent models were evaluated against the AI-assisted golden set.

---

## 6. What Is Misleading About My Headline Number?

The headline intent accuracy (85.5%–86.0%) should **not** be interpreted as a human-verified benchmark score due to several deliberate engineering caveats:

1. **AI-Assisted Golden Set**: The 200 evaluation examples were generated using automated heuristic stratification. They were not independently hand-annotated from scratch by a human.
2. **Weak Supervision Alignment**: The TF-IDF + Logistic Regression baseline was trained on weakly supervised heuristic labels. Its high accuracy partly reflects learning the exact same heuristic patterns used to stratify the golden set.
3. **Escalation Policy Deflection**: The system's conservative escalation rules safely route difficult, multi-turn, or ambiguous queries to humans (`ESCALATE`). While this ensures production safety, it means the agent only auto-handles cases where confidence is high.
4. **Retrieval Proxy Limitations**: Measuring retrieval by intent-match similarity is an automated heuristic proxy, not a true human judgment of whether the retrieved precedent provided sufficient context to solve the customer's problem.
5. **Reply Quality Human Agreement Not Measured**: While a genuine LLM-as-a-Judge system has been implemented, human-vs-LLM inter-rater reliability (Cohen's Kappa / correlation) was not measured in this submission due to uncompleted human review samples.

---

## 7. Failure Analysis: Five Real Examples

Below are five concrete failure cases extracted directly from the end-to-end evaluation results (`results/end_to_end_predictions.csv`):

### 1. Weak Retrieval (No Grounding)
* **Tweet ID**: `545729`
* **Failure Mode**: Weak Retrieval (No Grounding)
* **Customer Message**:
  > *"@AmazonHelp Don't hear from the 3rdparty seller in 2business days.Every time i call back it's the same thing.The last time i called they said they filed a claim&amp; i should hear something in 24 hours that was the 15th of November. Still nothing.Called this morning&amp;they hung up after 20min hold"*
* **Model's Generated Reply**:
  > *"I understand your issue regarding customer service complaint. @478180 I'm sorry, Roxanne, would you mind elaborating? Is there something we may assist with? Please let us know. ^AI"*
* **Why it Failed**: The hybrid retriever failed to locate similar examples with similarity score $\ge 0.30$, triggering `grounding_status: NONE`.
* **Hypothesis**: The complex, multi-sentence narrative detailing third-party seller timelines diluted lexical and semantic similarity against short, historical resolution tweets.
* **Proposed Fix**: Implement query summarization prior to retrieval, expand historical thread context windows, or lower retrieval thresholds for complaint routing.

### 2. Intent Misclassification
* **Tweet ID**: `2142987`
* **Failure Mode**: Intent Misclassification
* **Customer Message**:
  > *"@115821 is this your version of a joke?  Did you really just send me an empty bag? https://t.co/BonAl7yxIv"*
* **True Intent**: `DAMAGED_MISSING_ITEM` | **Predicted Intent**: `OTHER`
* **Model's Generated Reply**:
  > *"I understand your issue regarding other. @382869 If you're not worried about sock-gnomes, you can cancel your order if it hasn't entered shipping here: https://t.co/3kQwjObgTc ^AI"*
* **Why it Failed**: The model misclassified colloquial/sarcastic missing-item phrasing as `OTHER`, outputting an irrelevant reply about order cancellation.
* **Hypothesis**: The weak-supervision training pipeline relied on explicit keywords (e.g., "broken", "missing", "damaged"). Idiomatic complaints ("empty bag", "joke") lacked explicit token overlap.
* **Proposed Fix**: Fine-tune an intent classifier or use few-shot LLM intent classification with idiomatic few-shot demonstrations.

### 3. Conservative Complaint Escalation
* **Tweet ID**: `1018224`
* **Failure Mode**: Policy Hard-Escalation
* **Customer Message**:
  > *"@AmazonHelp @115850 Thank you so much for the worst product as well as worst Your Agent said he can't help me talked with rude (1/2)"*
* **True Intent**: `CUSTOMER_SERVICE_COMPLAINT` | **Predicted Intent**: `CUSTOMER_SERVICE_COMPLAINT`
* **Model's Generated Reply**:
  > *"I understand your issue regarding customer service complaint. @206653 I'm sorry about the situation. We'd like to help you, kindly connect with us here: https://t.co/vlvfJr4nN9 ^AI"*
* **Decision & Reason**: `ESCALATE` (*"Serious customer complaint detected."*)
* **Why it Failed (Policy Trade-off)**: The system immediately routed the complaint to a human agent without offering an initial automated de-escalation reply or gathering ticket information.
* **Hypothesis**: The escalation rule prioritizes risk aversion over automation rate, treating all expressions of dissatisfaction as immediate handoffs.
* **Proposed Fix**: Implement a multi-stage escalation workflow: generate an empathetic de-escalation response and collect order verification details before routing the ticket to a human agent.

### 4. Unsupported Action Escalation
* **Tweet ID**: `2399207`
* **Failure Mode**: Unsupported Action Escalation
* **Customer Message**:
  > *"@AmazonHelp Do you mean email customer service or use the website to cancel the order. This loaded when I clicked on cancel order. https://t.co/G3p0hhRKvi"*
* **True Intent**: `ORDER_MODIFICATION` | **Predicted Intent**: `ORDER_MODIFICATION`
* **Model's Generated Reply**:
  > *"I understand your issue regarding order modification. @181821 We request you to contact us using this link: https://t.co/GmYPWj1ew5 so we could help you cancel the order. ^AI"*
* **Decision & Reason**: `ESCALATE` (*"Weak or no historical grounding found."*)
* **Why it Failed**: The customer requested an action (order cancellation) that the agent cannot natively perform.
* **Hypothesis**: Without authenticated tool execution capabilities, the agent cannot inspect order states or trigger cancellations, forcing generic redirect links.
* **Proposed Fix**: Integrate authenticated tool calling with strict customer confirmation steps (e.g., `cancel_order_tool`).

### 5. Over-escalation on Ambiguous Follow-ups / Non-English Content
* **Tweet ID**: `1828696`
* **Failure Mode**: Language Mismatch & Context Escalation
* **Customer Message**:
  > *"バイスを春に買ったせいでAmazonから定期的に工具を勧められるのなんとかならない？"* *(Translation: "Can something be done about Amazon repeatedly recommending tools just because I bought a vise in the spring?")*
* **True Intent**: `OTHER` | **Predicted Intent**: `OTHER`
* **Model's Generated Reply**:
  > *"@262653 Just to make sure, did we go over setting the new payment method as the default in your account here: https://t.co/30Na205Fec ^AI"*
* **Decision & Reason**: `ESCALATE` (*"Weak or no historical grounding found."*)
* **Why it Failed**: The pipeline classified the query as `OTHER` but retrieved an irrelevant payment method snippet, escalating due to lack of grounding.
* **Hypothesis**: English language filtering during initial preprocessing failed to exclude non-English text, and the retrieval corpus contained no matching Japanese support precedents.
* **Proposed Fix**: Introduce an explicit language detection filter at pipeline entry, routing non-English queries to specialized language agents.

---

## 8. What I Would Do With One More Week

Given an additional week, development would focus on the following prioritized engineering tasks:

1. **Human-Annotated Golden Benchmark**: Replace the AI-assisted 200-example evaluation set with a genuinely hand-labelled benchmark, cross-annotated by two independent human reviewers with inter-annotator agreement (Cohen's Kappa) reported.
2. **Human-vs-LLM Agreement Study**: Complete the manual review of `evaluation/reply_quality_human_review.csv` and report Pearson, Spearman, and weighted Kappa metrics with 95% confidence intervals.
3. **Safe Tool Integration**: Implement function-calling tools (e.g., order lookup, address change, delivery rescheduling) with confirmation boundaries and dry-run execution.
4. **Retrieval Reranking**: Upgrade retrieval from basic hybrid fusion to a cross-encoder reranker (e.g., `bge-reranker-base`) to improve context relevance for complex queries.
5. **Model Distillation / Fine-Tuning**: Fine-tune a lightweight open-source model (e.g., Llama 3.2 3B or Mistral 7B) on support conversations to eliminate cloud LLM latency and API costs.
6. **Production Observability**: Add OpenTelemetry tracing across retrieval, confidence scoring, and escalation decisions with Prometheus KPI tracking.

---

## 9. Quick Start & Reproducibility

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/tanisha2601/hiver-ai-support-agent.git
cd hiver-ai-support-agent

python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Open .env and add your OPENAI_API_KEY (optional for baselines and tests; required for live LLM Judge)
```

### 3. Run Automated Tests
```bash
python -m pytest
```
*(Runs 27 offline unit and regression tests in under 20 seconds).*

### 4. Run Intent & Baseline Evaluations
```bash
# Run Majority Baseline
python -m src.intent.majority_baseline

# Run TF-IDF + Logistic Regression Baseline
python -m src.intent.tfidf_logreg_baseline

# Run Full Agent Pipeline Evaluation
python -m src.evaluation.evaluate_agent
```

### 5. Run LLM-as-a-Judge Evaluation
```bash
# Evaluate a fast sample of 30 examples with fixed seed
python -m src.evaluation.run_llm_judge --limit 30 --seed 42

# Full evaluation across all generated responses
python -m src.evaluation.run_llm_judge
```

### 6. Run Human-vs-LLM Agreement
```bash
python -m src.evaluation.llm_human_agreement
```

### 7. Start Interactive Services
```bash
# Start FastAPI backend
python -m uvicorn api.main:app --reload --port 8000

# In a separate terminal, start React frontend
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173` to test live queries in the interactive UI.

---

## 10. API Endpoints

* **`POST /api/agent/run`**: Executes the full agent pipeline.
  * **Payload**: `{"message": "string", "context": "optional string"}`
  * **Response**: `intent`, `intent_confidence`, `retrieved_examples`, `grounding_status`, `grounding_score`, `response`, `decision`, `decision_reason`.
* **`GET /`**: Health check and configuration status.
* **`GET /api/evaluation/summary`**: Returns parsed evaluation metrics for dashboard display.

---

## 11. Limitations

* **Provisional Labels**: Evaluation labels are AI-assisted and heuristic; they are not human-verified ground truth.
* **Weak Supervision**: The baseline classifier was trained on heuristic pseudo-labels.
* **Retrieval Proxy**: Intent-match accuracy is an automated proxy, not a substitute for human context assessment.
* **Human Agreement Sample Incomplete**: Human-vs-LLM alignment was not formally measured in this submission.
* **No Live Transaction Execution**: The agent cannot execute real refunds, address updates, or order cancellations.
* **Static Corpus**: Historical Twitter support conversations reflect public 2017 data and lack modern internal CRM context.
* **Full Index Rebuild Compute**: Running automated tests and evaluating existing datasets takes under 1 minute; however, recomputing semantic embeddings from scratch across the full 750MB raw Kaggle dataset (178,000+ tweets) requires substantial compute and is not guaranteed to finish under 15 minutes on standard hardware.
* **Conservative Escalation**: High escalation rates reduce the automated resolution rate on nuanced or complex tickets.

---

## 12. Dataset & License Notice

This project utilizes historical Twitter customer support interactions from the [Kaggle Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) dataset. The raw dataset is excluded from version control in compliance with platform terms of service. All project source code is provided for evaluation purposes.
