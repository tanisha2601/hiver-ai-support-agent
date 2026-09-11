from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import agent, evaluation, health

app = FastAPI(
    title="Hiver AI Support Agent API",
    description="API for analyzing customer requests and serving evaluation metrics.",
    version="1.0.0"
)

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["Evaluation"])
