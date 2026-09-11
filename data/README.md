# Hiver AI Support Agent - Data

## Dataset Source
This project uses a subset of the **Customer Support on Twitter** dataset, originally sourced from Kaggle. 

- **Brand Selected**: AmazonHelp
- **Rationale**: AmazonHelp was selected due to its high volume of support interactions, comprehensive coverage of customer complaints, and the strong presence of historical brand responses suitable for building an AI-assisted retrieval corpus.

## Data Usage Policy & Git Tracking
**IMPORTANT**: The raw Kaggle dataset (`twcs.csv`, `archive.zip`) is intentionally **NOT** committed to this repository. This is to keep the repository lightweight and respect original licensing constraints.

All `data/raw/*`, `data/interim/*`, and `data/processed/*` files are ignored via `.gitignore` except for necessary `.gitkeep` files. 

## How to Reproduce
To recreate the data pipeline:
1. Download the `twcs.csv` dataset from [Kaggle Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter).
2. Place the `twcs.csv` file into `data/raw/twcs.csv`.
3. Run the preprocessing script:
   ```bash
   python -m src.data.preprocess
   ```
4. This will generate the clean, reconstructed conversation threads in the `data/processed/` directory.
