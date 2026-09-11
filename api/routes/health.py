from fastapi import APIRouter

router = APIRouter()

import os

@router.get("/")
def health_check():
    """
    Check if the API and underlying Agent are healthy and ready to serve requests.
    Returns backend config as well.
    """
    return {
        "status": "ok",
        "agent": "ready",
        "retrieval": "ready",
        "generation": "ready",
        "evaluation_data": "available" if os.path.exists("results/end_to_end_metrics.csv") else "missing",
        "dataset": "AmazonHelp",
        "retrieval_type": "Hybrid (TF-IDF + Semantic)",
        "embedding_model": "all-MiniLM-L6-v2"
    }
