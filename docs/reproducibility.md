# Reproducibility Guide

Follow these exact steps to run tests, execute evaluations, and reproduce the Hiver AI Support Agent pipeline.

---

## 1. Environment Setup

Clone the repository and set up a Python virtual environment:

```bash
git clone https://github.com/tanisha2601/hiver-ai-support-agent.git
cd hiver-ai-support-agent

python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
```

Set up your environment variables:
```bash
cp .env.example .env
# Edit .env and configure your OPENAI_API_KEY (required for live LLM Judge and generation)
```

---

## 2. Run Automated Test Suite

Verify system integrity, schema validation, and evaluation logic:
```bash
python -m pytest
```
*(Runs all 27 unit and regression tests offline without external API dependencies).*

---

## 3. Run Intent & Baseline Evaluations

Execute the intent classification baseline and agent evaluations:

### A. Majority-Class Baseline
```bash
python -m src.intent.majority_baseline
```
*(Evaluates the dominant-class statistical floor, producing `results/majority_baseline_metrics.csv`)*

### B. TF-IDF + Logistic Regression Baseline
```bash
python -m src.intent.tfidf_logreg_baseline
```
*(Evaluates the classical ML baseline under Text-Only and Text+Context variants)*

### C. End-to-End Agent Evaluation
```bash
python -m src.evaluation.evaluate_agent
```
*(Evaluates the full agent pipeline over the 200 evaluation examples, generating `results/end_to_end_metrics.csv` and `results/end_to_end_predictions.csv`)*

---

## 4. Run LLM-as-a-Judge Evaluation

Evaluate the quality of generated replies against the strict 1–5 rubric:

```bash
# Evaluate a fast sample of 30 stratified examples (deterministic seed)
python -m src.evaluation.run_llm_judge --limit 30 --seed 42

# Full evaluation across all examples
python -m src.evaluation.run_llm_judge
```
*(Outputs `results/llm_judge_scores.csv` and `results/llm_judge_metrics.csv`)*

---

## 5. Human-vs-LLM Agreement

To analyze alignment between human expert ratings and the LLM judge:

```bash
python -m src.evaluation.llm_human_agreement
```
*(Compares scores in `evaluation/reply_quality_human_review.csv` against `results/llm_judge_scores.csv`)*

---

## 6. Full Pipeline Reproduction from Raw Dataset (Optional)

If you wish to reconstruct conversation threads and rebuild indices from the raw Kaggle corpus:

1. Download `twcs.csv` from [Kaggle Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter).
2. Place the unzipped file at: `data/raw/twcs.csv`
3. Preprocess and reconstruct conversation threads:
   ```bash
   python -m src.data.preprocess
   ```
4. Build TF-IDF and Semantic retrieval embeddings:
   ```bash
   python -m src.retrieval.build_index
   ```

*(Note: Running the automated test suite and evaluating models takes under 1 minute using the provided evaluation dataset. Rebuilding the full semantic index from scratch across 178,000+ raw tweets takes substantial compute time and is not guaranteed to finish under 15 minutes on standard hardware).*

---

## 7. Start Interactive Services

### Backend API
```bash
python -m uvicorn api.main:app --reload --port 8000
```

### Frontend Dashboard
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173` to interact with the Support Agent and view the evaluation metrics dashboard.
