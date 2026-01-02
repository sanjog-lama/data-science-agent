"""Data Retrieval Agent - Simplified for data fetching only."""

import logging
from typing import Dict, Any, List
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from .prompts import get_retrieval_instruction

_logger = logging.getLogger(__name__)

def get_retrieval_agent(mcp_servers: List[Dict[str, Any]], 
                       model_config: Dict[str, Any]) -> Agent:
    """Create the data retrieval agent - fetches data only."""
    
    from ...tools import create_mcp_toolsets, get_lite_llm_model
    
    # Create MCP toolsets
    mcp_toolsets = create_mcp_toolsets(mcp_servers)
    
    # Create model instance
    model = get_lite_llm_model(model_config)
    
    agent = Agent(
        name="data_retrieval_agent",
        model=model,
        instruction=get_retrieval_instruction(),
        description="Fetches data from various sources via MCP tools",
        tools=mcp_toolsets,
        # NO output schema - returns whatever the tools return
        before_agent_callback=retrieval_before_callback,
        after_tool_callback=retrieval_after_tool_callback
    )
    
    return agent

def retrieval_before_callback(callback_context: CallbackContext) -> None:
    """Retrieval agent callback: Extract query from state."""
    try:
        user_query = callback_context.state.get('original_user_query', '')
        if user_query:
            _logger.info(f"Retrieval agent processing: '{user_query[:80]}...'")
            callback_context.state['retrieval_query'] = user_query
    except Exception as e:
        _logger.error(f"Error in retrieval_before_callback: {e}")

def retrieval_after_tool_callback(tool, args, tool_context, tool_response):
    """Store tool response in state."""
    try:
        if tool_response:
            tool_context.state['raw_tool_response'] = tool_response
            _logger.info("Tool response stored in state")
    except Exception as e:
        _logger.error(f"Error in retrieval_after_tool_callback: {e}")
    return None