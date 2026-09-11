# Hiver AI Support Agent

An AI-powered customer-support agent that:
- classifies customer intent
- retrieves historically similar support conversations
- generates grounded responses
- decides AUTO_HANDLE vs ESCALATE
- provides evaluation and failure analysis

### Technology Stack
- **Frontend**: React + Vite + Recharts
- **Backend**: FastAPI + Python
- **ML/NLP**: TF-IDF, Logistic Regression, Semantic Embeddings, Hybrid Retrieval, LLM Response Generation
- **Evaluation**: AI-assisted stratified evaluation, Leakage-safe split, Baseline comparison, Retrieval evaluation, Reply-quality evaluation, Escalation analysis

## Dashboard Preview
*Screenshots can be found in `docs/screenshots/`*
- **Overview Dashboard**: High-level KPIs and metrics.
- **Support Agent**: Live pipeline testing.
- **Evaluation**: Baseline and final agent comparisons.
- **Retrieval**: Retrieval proxy metrics.
- **Failure Analysis**: Top failure modes.

## 1. Project Flow

```text
Customer Message
        ↓
Intent Classification
        ↓
Hybrid Retrieval
        ↓
Historical Support Evidence
        ↓
Grounding Assessment
        ↓
Response Generation
        ↓
Escalation Policy
        ↓
AUTO_HANDLE / ESCALATE
```
- **Intent Classification**: Predicts the query category (e.g. `DELIVERY_SHIPPING`).
- **Hybrid Retrieval**: Combines TF-IDF and Semantic embeddings to fetch past resolutions.
- **Historical Support Evidence**: Context fed into the LLM.
- **Grounding Assessment**: Ensures the response is factually rooted in the evidence.
- **Response Generation**: Generates an empathetic brand reply.
- **Escalation Policy**: Safely routes risky or uncertain requests to a human agent.

## 2. Evaluation Results
> **Methodology Note**: The evaluation set is AI-assisted and stratified rather than manually verified by human annotators. Results should therefore not be interpreted as human-validated benchmark accuracy.

| Model | Accuracy | Macro F1 | Weighted F1 |
|---|---:|---:|---:|
| Majority Baseline | 12.5% | 2.5% | 2.8% |
| TF-IDF + LogReg (Text + Context) | 86.0% | 86.3% | 86.0% |
| Final Agent | 85.5% | 86.0% | 85.6% |

The baseline reported above reflects the Text + Context variant (the Text-Only variant achieved 89.5%), but both are weakly supervised and should not be interpreted as human-validated benchmark accuracy.

*Limitation*: The TF-IDF baseline was trained on weakly supervised heuristics and might overfit instead of learning semantic meaning.

## 3. Failure Analysis

| Failure Mode | Cause | Improvement |
|---|---|---|
| Weak Retrieval (No Grounding) | Hybrid retriever could not find similar examples above minimum threshold. | Increase historical corpus size or lower threshold for safe intents. |
| Intent Misclassification | Weak-supervision trained model failed on overlapping vocabulary (e.g. delivery vs damaged). | Gather manually annotated data or use semantic classifier. |
| Conservative Complaint Escalation | Policy explicitly hard-escalates serious complaints regardless of confidence. | Allow empathetic de-escalation reply before routing. |
| Unsupported Action Escalation | User requested an action the agent cannot natively perform. | Implement API tool calling to modify orders. |
| Over-escalation on Ambiguous Follow-ups | Short messages correctly classified but lacked context signal. | Build entity extractor to check for tracking IDs. |

## 4. Quick Start

### 1. Clone
```bash
git clone https://github.com/tanisha2601/hiver-ai-support-agent.git
cd hiver-ai-support-agent
```

### 2. Install backend
```bash
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
```
*(Open `.env` and configure your necessary API keys. Never commit real credentials.)*

### 4. Obtain dataset
Download `twcs.csv` from [Kaggle Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter). Place the file exactly at: `data/raw/twcs.csv`
*(Do not commit this file.)*

### 5. Start backend
```bash
python -m uvicorn api.main:app --reload --port 8000
```

### 6. Start frontend
```bash
cd frontend
npm install
npm run dev
```

### 7. Open
Navigate to [http://localhost:5173](http://localhost:5173) in your browser.

## 5. API Endpoints

### Run Pipeline
`POST /api/agent/run`
- **Input**:
  - `message`: string (customer message)
  - `context`: string (optional previous context)
- **Output**:
  - `intent`: string
  - `intent_confidence`: float
  - `retrieved_examples`: list
  - `grounding_status`: string
  - `grounding_score`: float
  - `response`: string
  - `decision`: string
  - `decision_reason`: string

### Health & Config
`GET /` (Health check and model config)

### Metrics Aggregation
`GET /api/evaluation/summary` (Returns parsed CSV results for the frontend)

## 6. Engineering Highlights
- **conversation reconstruction from tweet reply relationships**
- **leakage-safe evaluation split at conversation level**
- **hybrid semantic + lexical retrieval**
- **retrieval blacklisting of evaluation conversations**
- **grounded response generation**
- **explicit escalation policy**
- **evaluation baselines**
- **failure analysis**
- **FastAPI + React integration**
- **automated tests**
- **reproducibility documentation**

## 7. Limitations
- AI-assisted rather than human-validated evaluation labels
- weakly supervised TF-IDF baseline
- retrieval intent-match is a proxy metric
- historical Twitter dataset limits real-time action context
- no real customer account access
- no production CRM integration
- conservative escalation behavior restricts auto-handling

## 8. License & Dataset Notice
The source code is provided as-is. The dataset used in this project originates from Kaggle and is subject to Twitter/X's terms of service and the dataset author's licensing constraints. It is strictly excluded from version control.
