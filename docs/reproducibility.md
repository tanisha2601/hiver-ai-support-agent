# Reproducibility Guide

Follow these exact steps to reproduce the Hiver AI Support Agent pipeline from scratch.

## 1. Environment Setup

Clone the repository and set up a Python 3 virtual environment:

```bash
git clone <repository_url> hiver-ai-support-agent
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
# Edit .env and add your OPENAI_API_KEY
```

## 2. Obtain Dataset
Download the `twcs.csv` dataset from [Kaggle Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter).

Place the unzipped file in the correct directory:
```
hiver-ai-support-agent/data/raw/twcs.csv
```

## 3. Data Preprocessing & Reconstruction
Run the preprocessing script to filter for AmazonHelp and reconstruct conversation threads:
```bash
python -m src.data.preprocess
```
*(This generates `amazon_train_pool.csv` and `amazon_eval.csv` in `data/processed/`)*

## 4. Build Retrieval Index
Build the TF-IDF and Semantic embeddings for the historical corpus:
```bash
python -m src.retrieval.build_index
```
*(This will generate necessary `.pkl` and `.npy` artifacts in `data/processed/retrieval/`)*

## 5. Generate Evaluation Artifacts
Run the evaluation scripts to recreate the baseline and agent metrics:
```bash
python -m src.evaluation.evaluate_baselines
python -m src.evaluation.evaluate_end_to_end
```
*(This will populate the `results/` directory with classification reports and predictions)*

## 6. Start Services

### Backend
Start the FastAPI server:
```bash
python -m uvicorn api.main:app --reload --port 8000
```

### Frontend
In a separate terminal, start the React application:
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173` to view the dashboard and interact with the Support Agent.
