"""Data Retrieval Agent with MCP integration."""

import logging
from typing import Dict, Any, List
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from .prompts import get_retrieval_instruction

_logger = logging.getLogger(__name__)

def get_retrieval_agent(mcp_servers: List[Dict[str, Any]], 
                       model_config: Dict[str, Any]) -> Agent:
    """Create the data retrieval agent."""
    
    from ...tools import create_mcp_toolsets, get_lite_llm_model
    
    mcp_toolsets = create_mcp_toolsets(mcp_servers)
    
    # Create model instance
    model = get_lite_llm_model(model_config)
    
    agent = Agent(
        name="data_retrieval_agent",
        model=model,
        instruction=get_retrieval_instruction(),
        description="Retrieves data from PostgreSQL, MSSQL, HubSpot, and metadata systems via MCP",
        tools=mcp_toolsets,
        output_key="retrieved_data",
        before_agent_callback=retrieval_before_callback,
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
            # Try to get from current message as fallback
            if hasattr(callback_context, 'current_message'):
                current_msg = callback_context.current_message
                if hasattr(current_msg, 'text'):
                    callback_context.state['retrieval_query'] = current_msg.text
                    _logger.info(f"Retrieval agent using current message: '{current_msg.text[:80]}...'")
            
    except Exception as e:
        _logger.error(f"Error in retrieval_before_callback: {e}")