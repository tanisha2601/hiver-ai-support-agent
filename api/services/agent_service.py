from src.agent import run_agent

def execute_agent_pipeline(message: str, context: str = None) -> dict:
    """
    Thin wrapper around the existing Python AI pipeline.
    Calls `run_agent` from `src.agent`.
    """
    # The existing pipeline expects optional context. 
    # Returns a dictionary matching the schema perfectly.
    result = run_agent(customer_message=message, context=context)
    return result
