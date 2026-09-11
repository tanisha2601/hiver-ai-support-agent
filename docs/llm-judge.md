# LLM-as-a-Judge Reply Quality Evaluation

This document defines the methodology, scoring rubric, prompt architecture, and agreement validation framework for evaluating generated customer support replies using an LLM judge.

---

## 1. Important Methodology Disclosure

> **Transparency Note**: 
> - The 200 intent evaluation examples in this repository were curated using AI-assisted heuristic pseudo-labels and are **not independently hand-labelled from scratch**.
> - The previous reply quality metric in this repository was an automated **heuristic proxy** (derived from string length and status flags).
> - This document introduces a **real LLM-as-a-Judge** system. To validate judge calibration against human discernment, a dedicated **human agreement sample (~30 examples)** is provided in `evaluation/reply_quality_human_review.csv`.
> - The human agreement sample is intended solely to validate judge alignment on reply quality, **not** to retroactively claim that all 200 intent classification examples were manually annotated.

---

## 2. Reply Quality Scoring Rubric (1–5 Scale)

Each generated response is evaluated across five granular dimensions and one overall score:

### A. Relevance
* **5**: Directly addresses the customer's actual issue with no extraneous tangents.
* **4**: Mostly addresses the issue with minor irrelevant content or slight drift.
* **3**: Partially addresses the issue; touches on the topic but misses key customer pain points.
* **2**: Weakly related; largely misses the core intent or addresses a wrong sub-problem.
* **1**: Completely irrelevant or off-topic.

### B. Helpfulness
* **5**: Gives a clear, actionable, and concrete path forward or resolution.
* **4**: Useful and actionable, but missing a minor detail or step.
* **3**: Somewhat useful, but incomplete, requiring additional customer turns.
* **2**: Vague, generic, or minimally helpful boilerplate.
* **1**: Completely unhelpful; wastes customer effort or offers counterproductive guidance.

### C. Groundedness
* **5**: All assertions, recommended actions, and policy statements are strongly supported by the provided historical support evidence.
* **4**: Mostly grounded with very minor unsupported phrasing that remains safe.
* **3**: Mixed grounding; some elements align with past precedent, while others have no grounding evidence.
* **2**: Significant unsupported assertions or actions that contradict support precedent.
* **1**: Largely unsupported or directly contradicts historical evidence.

### D. Clarity
* **5**: Crisp, concise, professional, and effortless to read.
* **4**: Clear and understandable, with minor verbosity or repetitive phrasing.
* **3**: Understandable, but noticeably wordy, awkward, or slightly confusing.
* **2**: Difficult to follow; poorly structured or ambiguous phrasing.
* **1**: Incoherent, garbled, or completely unclear.

### E. Unsupported Claims / Hallucination
* **5**: Zero unsupported claims; strictly stays within stated evidence and safe routing.
* **4**: Very minor speculative wording with no impact on customer outcome or policy.
* **3**: One questionable claim (e.g., unsubstantiated delivery window or unverified policy).
* **2**: Multiple unsupported claims (e.g., promising a refund or claim filing not present in evidence).
* **1**: Substantial fabrication (inventing monetary compensation, tracking IDs, or fake policies).

### Overall Score (1–5)
A holistic synthesis of the above dimensions:
* **5 (Excellent)**: Fully grounded, empathetic, actionable, and safe.
* **4 (Good)**: Minor wording imperfections, but safe and effective.
* **3 (Marginal)**: Partial resolution or weak grounding; acceptable only with human escalation.
* **2 (Poor)**: Hallucinatory, ungrounded, or misdirected.
* **1 (Unacceptable)**: Detrimental, fabricated claims, or severe policy violation.

---

## 3. Judge Prompt Architecture

The evaluator is governed by the versioned prompt in [`src/evaluation/prompts.py`](file:///d:/hiver-ai-support-agent/src/evaluation/prompts.py).

Key principles enforced in the prompt:
1. **Evidence-Conditioned**: The prompt explicitly reminds the judge: *"Groundedness means that the response is supported by the provided evidence, not that it sounds plausible."*
2. **Anti-Eloquence Bias**: The judge is strictly commanded: *"Do not reward a response merely because it sounds professional."*
3. **Severe Penalties**: Explicit penalties are enforced for fabricated timelines, unverified refunds, and unsupported promises.
4. **Structured JSON**: Enforces deterministic, schema-validated JSON containing scores `1–5` and a concise `reason`.

---

## 4. Model & API Configuration

The judge reuses the project's standard configuration conventions:
* `OPENAI_API_KEY`: Required environment variable for API authentication.
* `OPENAI_BASE_URL`: API base URL (defaults to `https://api.openai.com/v1`, supporting OpenAI, Azure, Groq, Ollama, OpenRouter).
* `LLM_MODEL`: Evaluation model (defaults to `gpt-4o-mini`).
* **Deterministic Decoding**: Temperature is locked to `0.0` for reproducibility.
* **Fail-Fast Safety**: If `OPENAI_API_KEY` is missing, the judge halts with an actionable error. It **never** falls back to heuristic proxies.

---

## 5. Evaluation Procedure

### Running the LLM Judge
To evaluate generated replies across the dataset:
```bash
# Evaluate a fast sample of 30 examples
python -m src.evaluation.run_llm_judge --limit 30 --seed 42

# Evaluate all generated replies
python -m src.evaluation.run_llm_judge
```

Outputs generated:
* Detailed scores per example: `results/llm_judge_scores.csv`
* Aggregate rubric averages: `results/llm_judge_metrics.csv`

---

## 6. Human Agreement Procedure

To establish whether the LLM judge mirrors human standards:

1. **Stratified Sample**: `evaluation/reply_quality_human_review.csv` contains 30 representative examples stratified across intent types.
2. **Human Review Tool**:
   ```bash
   python -m src.evaluation.reply_quality_reviewer
   ```
   Allows rapid manual scoring (1–5 keys) without auto-filling or fabricating human scores.
3. **Calculate Agreement Metrics**:
   ```bash
   python -m src.evaluation.llm_human_agreement
   ```
   Computes:
   * Mean human score vs. Mean LLM score
   * Exact agreement percentage ($Human = LLM$)
   * Adjacent agreement percentage ($|Human - LLM| \le 1$)
   * Spearman rank correlation ($\rho$)
   * Pearson correlation ($r$)
   * Cohen's Weighted / Unweighted Kappa ($\kappa$)
   * Dimension-by-dimension agreement breakdown

---

## 7. Known Limitations

1. **Sample Size**: A sample of 30 human reviews provides directional alignment indicators, but has wide confidence intervals. It should not be cited as definitive statistical proof of universal human alignment.
2. **Deterministic Baseline History**: The Twitter customer support responses in the dataset frequently direct customers to private direct messages (DMs). The LLM judge must discern between generic corporate redirects and true resolution guidance.
3. **Self-Consistency**: LLMs may exhibit positional or length biases when judging text. The prompt's strict adherence to grounding penalties mitigates but does not fully eliminate these tendencies.
