from fastapi import APIRouter
from api.schemas.agent import AgentRequest, AgentResponse
from api.services.agent_service import execute_agent_pipeline

router = APIRouter()

@router.post("/run", response_model=AgentResponse)
def run_agent_endpoint(request: AgentRequest):
    """
    Run the end-to-end AI Support Agent pipeline for a given customer message.
    """
    result = execute_agent_pipeline(request.message, request.context)
    return result
