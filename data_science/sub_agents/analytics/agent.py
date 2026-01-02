"""Data Analytics Agent for analysis and visualization."""

import logging
import json
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext

# Import the simplified schema
from ...response import AnalyticsResponseSchema
from .prompts import get_analytics_instruction

_logger = logging.getLogger(__name__)


def get_analytics_agent(model_config: Dict[str, Any]) -> Agent:
    """Create the data analytics agent with simplified schema."""
    
    from ...tools import get_lite_llm_model
    
    model = get_lite_llm_model(model_config)
    
    agent = Agent(
        name="data_analytics_agent",
        model=model,
        instruction=get_analytics_instruction(),
        description="Analyzes data and creates visualization recommendations",
        tools=[],
        output_schema=AnalyticsResponseSchema,  # Use simplified schema
        output_key="analytics_response",
        before_agent_callback=analytics_before_callback,
        after_agent_callback=analytics_after_callback
    )
    
    return agent


def analytics_before_callback(callback_context: CallbackContext) -> None:
    """Prepare data for analysis."""
    try:
        # Get data from retrieval agent
        retrieved_data = callback_context.state.get('retrieval_response', {})
        raw_response = retrieved_data.get('raw_response', {})
        user_query = callback_context.state.get('original_user_query', '')
        
        _logger.info(f"Analytics agent processing: '{user_query[:80]}...'")
        _logger.info(f"Analytics agent retrieval_response: '{retrieved_data[:80]}...'")
        
        
        if raw_response:
            # Store query for the agent to use
            callback_context.state['analytics_query'] = user_query
            callback_context.state['analytics_data'] = raw_response
            
            # Also add a simple summary to help the agent
            data_summary = get_data_summary(raw_response)
            callback_context.state['data_summary'] = data_summary
            
            _logger.info(f"Data summary: {data_summary}")
        else:
            _logger.warning("No data available for analytics")
            
    except Exception as e:
        _logger.error(f"Error in analytics_before_callback: {e}")


def get_data_summary(data: Any) -> Dict[str, Any]:
    """Create a simple summary of the data."""
    try:
        if isinstance(data, dict):
            if 'rows' in data and 'columns' in data:
                # SQL result format
                return {
                    "type": "sql_result",
                    "row_count": len(data['rows']),
                    "columns": data['columns'],
                    "sample": data['rows'][:2] if data['rows'] else []
                }
            else:
                # Generic dict
                return {
                    "type": "dict",
                    "keys": list(data.keys()),
                    "size": len(data)
                }
        elif isinstance(data, list):
            return {
                "type": "list",
                "count": len(data),
                "sample": data[:2] if data else []
            }
        elif isinstance(data, str):
            return {
                "type": "string",
                "length": len(data),
                "is_json": is_valid_json(data)
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)
            }
    except:
        return {"type": "unknown", "error": "Could not summarize"}


def is_valid_json(text: str) -> bool:
    """Check if text is valid JSON."""
    try:
        json.loads(text)
        return True
    except:
        return False


def analytics_after_callback(callback_context: CallbackContext) -> None:
    """Clean up after analysis."""
    try:
        # Clean up temporary data
        cleanup_keys = ['analytics_query', 'analytics_data', 'data_summary']
        for key in cleanup_keys:
            callback_context.state.pop(key, None)
        
        _logger.info("Analytics agent cleanup completed")
        
    except Exception as e:
        _logger.error(f"Error in analytics_after_callback: {e}")