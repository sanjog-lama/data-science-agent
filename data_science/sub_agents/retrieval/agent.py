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
        after_tool_callback=retrieval_after_tool_callback
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

def retrieval_after_tool_callback(tool, args, tool_context, tool_response):
    """Store retrieval results in state."""
    try:
        if tool_response and isinstance(tool_response, dict):
            formatted = format_retrieval_results(tool_response)

            # Detect if user query implies chart/graph
            user_query = tool_context.state.get('original_user_query', '')
            needs_chart = any(
                kw in user_query.lower()
                for kw in ["chart", "graph", "plot", "visualize", 
                           "bar", "line", "pie", "scatter", "histogram"]
            )

            # Store both in state, plus needs_chart flag
            tool_context.state['retrieved_raw_data'] = formatted["raw"]
            tool_context.state['retrieved_data'] = {
                "structured": formatted["structured"],
                "needs_chart": needs_chart
            }

            _logger.info("Retrieval results stored in state with needs_chart=%s", needs_chart)

    except Exception as e:
        _logger.error(f"Error in retrieval_after_tool_callback: {e}")

    return None


def format_retrieval_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format retrieval results for analytics agent consumption.
    
    Returns a dict with:
      - 'structured': JSON/table suitable for AnalyticsProcessor
      - 'raw': human-readable string for users who just want data
    """
    try:
        output = {"structured": None, "raw": ""}

        if 'rows' in results and 'columns' in results:
            columns = results['columns']
            rows = results['rows']

            # Structured JSON for analytics
            output["structured"] = {
                "type": "table",
                "headers": columns,
                "rows": rows,
                "row_count": len(rows),
                "column_count": len(columns)
            }

            # Raw text preview for user
            sample_size = min(5, len(rows))
            raw_text = f"Retrieved {len(rows)} rows with {len(columns)} columns\n"
            raw_text += "Columns: " + ", ".join(columns) + "\n\n"
            raw_text += f"Sample rows ({sample_size} of {len(rows)}):\n"
            for i in range(sample_size):
                raw_text += f"Row {i+1}: {dict(zip(columns, rows[i]))}\n"
            output["raw"] = raw_text

        elif 'data' in results:
            output["raw"] = str(results['data'])[:2000]
            output["structured"] = {"type": "json", "data": results['data']}

        else:
            output["raw"] = str(results)[:1000]

        return output

    except Exception as e:
        _logger.error(f"Error formatting retrieval results: {e}")
        return {"structured": None, "raw": str(results)}