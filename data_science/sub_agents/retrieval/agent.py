"""Data Retrieval Agent - Simplified for data retrieval."""

import logging
from typing import Dict, Any, List
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from .prompts import get_retrieval_instruction

_logger = logging.getLogger(__name__)


def get_retrieval_agent(mcp_servers: List[Dict[str, Any]], 
                       model_config: Dict[str, Any]) -> Agent:
    """Create the data retrieval agent - simplified for data only."""
    
    from ...tools import create_mcp_toolsets, get_lite_llm_model
    
    # Create MCP toolsets
    mcp_toolsets = create_mcp_toolsets(mcp_servers)
    
    # Create model instance
    model = get_lite_llm_model(model_config)
    
    # Simplified agent without output schema - returns raw data
    agent = Agent(
        name="data_retrieval_agent",
        model=model,
        instruction=get_retrieval_instruction(),
        description="Retrieves data from PostgreSQL, MSSQL, HubSpot, and metadata systems via MCP",
        tools=mcp_toolsets,
        # before_agent_callback=retrieval_before_callback,
        # after_tool_callback=retrieval_after_tool_callback,
        # output_key="retrieval_response"
    )
    
    return agent


def retrieval_before_callback(callback_context: CallbackContext) -> None:
    """Retrieval agent callback: Extract query from state."""
    try:
        # Get the user query from session state (set by root agent)
        user_query = callback_context.state.get('original_user_query', '')
        
        if user_query:
            _logger.info(f"Retrieval agent processing query: '{user_query[:80]}...'")
            # Store in agent-specific state
            callback_context.state['retrieval_query'] = user_query
        else:
            _logger.warning("No user query found in state for retrieval agent")
            
    except Exception as e:
        _logger.error(f"Error in retrieval_before_callback: {e}")


# def retrieval_after_tool_callback(tool, args, tool_context, tool_response):
#     """Store retrieval results in state for analytics agent."""
#     try:
#         if tool_response:
#             # Store the response in a standardized format for analytics agent
#             # This could be the raw response or a processed version
#             tool_context.state['retrieved_data'] = {
#                 'raw_response': tool_response,
#                 'tool_used': tool.name if hasattr(tool, 'name') else str(tool),
#                 'args_used': args
#             }
#             _logger.info(f"Retrieved data stored in state from tool: {tool}")
            
#     except Exception as e:
#         _logger.error(f"Error in retrieval_after_tool_callback: {e}")
    
#     return None