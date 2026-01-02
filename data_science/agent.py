"""Root Orchestrator Agent for Data Science System - Following ADK Patterns."""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from google.adk.models.lite_llm import LiteLlm

# Load environment
load_dotenv()

# Import sub-agents
from .sub_agents.retrieval.agent import get_retrieval_agent
from .response import StandardResponse, ResponseType

# Import prompts
from .prompts import get_root_instruction
from .tools import load_mcp_config, get_model_config

_logger = logging.getLogger(__name__)

# Global configurations (loaded once)
MCP_SERVERS = None
MODEL_CONFIG = None

def initialize_configurations():
    """Load configurations once."""
    global MCP_SERVERS, MODEL_CONFIG
    if MCP_SERVERS is None:
        MCP_SERVERS = load_mcp_config()
    if MODEL_CONFIG is None:
        MODEL_CONFIG = get_model_config()
    return MCP_SERVERS, MODEL_CONFIG

def extract_query_from_content(content) -> str:
    """Extract text from user content."""
    if content and hasattr(content, 'parts') and content.parts:
        return content.parts[0].text
    return ""

def determine_response_type(query: str) -> ResponseType:
    """Determine response type based on query."""
    query_lower = query.lower()
    
    analysis_keywords = [
        'analyze', 'analysis', 'trend', 'pattern', 'insight',
        'visualize', 'chart', 'graph', 'plot', 'compare',
        'correlation', 'statistic', 'average', 'sum', 'total',
        'distribution', 'top', 'bottom', 'rank', 'percentage'
    ]
    
    metadata_keywords = [
        'list', 'tables', 'schema', 'metadata', 'structure',
        'describe', 'show tables', 'what tables'
    ]
    
    if any(keyword in query_lower for keyword in analysis_keywords):
        return ResponseType.ANALYSIS
    elif any(keyword in query_lower for keyword in metadata_keywords):
        return ResponseType.METADATA
    else:
        return ResponseType.RAW_DATA

def root_before_callback(callback_context: CallbackContext) -> None:
    """Root agent callback: Extract user query and determine response type."""
    try:
        # Extract user query
        user_content = callback_context.user_content
        user_query = extract_query_from_content(user_content)
        
        if user_query:
            _logger.info(f"Root agent extracted query: '{user_query[:80]}...'")
            
            # Determine response type
            response_type = determine_response_type(user_query)
            _logger.info(f"Determined response type: {response_type}")
            
            # Store in session state
            callback_context.state['original_user_query'] = user_query
            callback_context.state['response_type'] = response_type.value
            callback_context.state['query_timestamp'] = datetime.now().isoformat()
            
            _logger.info(f"Root agent stored query. Response type: {response_type}")
            
    except Exception as e:
        _logger.error(f"Error in root_before_callback: {e}")

def root_after_tool_callback(tool, args, tool_context, tool_response):
    """Format the tool response into standardized format."""
    try:
        if not tool_response:
            return None
        
        _logger.info(f"Formatting response from tool: {tool.name if hasattr(tool, 'name') else tool}")
        
        # Get response type from state
        response_type = tool_context.state.get('response_type', ResponseType.RAW_DATA.value)
        user_query = tool_context.state.get('original_user_query', 'Unknown query')
        
        # Parse the tool response (it might already be a dict or a string)
        if isinstance(tool_response, dict):
            parsed_response = tool_response
        elif isinstance(tool_response, str):
            try:
                # Try to parse as JSON
                parsed_response = json.loads(tool_response)
            except json.JSONDecodeError:
                # If it's not JSON, treat as text data
                parsed_response = {"text": tool_response}
        else:
            parsed_response = {"data": str(tool_response)}
        
        # Create standardized response
        if response_type == ResponseType.ANALYSIS.value:
            formatted_response = format_analysis_response(parsed_response, user_query)
        elif response_type == ResponseType.METADATA.value:
            formatted_response = format_metadata_response(parsed_response, user_query)
        else:  # RAW_DATA
            formatted_response = format_raw_data_response(parsed_response, user_query)
        
        # Convert to dict for ADK
        response_dict = formatted_response.dict()
        
        # Log the formatted response
        _logger.info(f"Formatted response type: {response_type}")
        
        # Return the formatted response
        return response_dict
        
    except Exception as e:
        _logger.error(f"Error in root_after_tool_callback: {e}")
        # Return error response
        error_response = StandardResponse(
            response_type=ResponseType.ERROR,
            message=f"Error processing response: {str(e)}",
            error=str(e)
        )
        return error_response.dict()

def format_analysis_response(data: Dict[str, Any], query: str) -> StandardResponse:
    """Format analysis response into standardized format."""
    try:
        # Extract insights if present
        insights = []
        if 'key_insights' in data:
            insights = data.get('key_insights', [])
        elif 'insights' in data:
            insights = data.get('insights', [])
        
        # Extract metrics
        metrics = []
        if 'computed_metrics' in data:
            metrics_data = data.get('computed_metrics', {})
            # Convert metrics to standard format
            metrics = convert_metrics_to_standard(metrics_data)
        
        # Extract visualization
        visualization = None
        if 'chart_recommendations' in data:
            chart_recs = data.get('chart_recommendations', [])
            if chart_recs:
                # Use first chart recommendation
                first_chart = chart_recs[0]
                visualization = {
                    "type": first_chart.get('chart_type', 'bar_chart'),
                    "title": first_chart.get('title', f"Analysis of {query}"),
                    "data_points": first_chart.get('data_points', []),
                    "insight": first_chart.get('insight', '')
                }
        
        # Extract recommendations
        recommendations = []
        if 'recommendations' in data:
            recs = data.get('recommendations', [])
            if isinstance(recs, list):
                if recs and isinstance(recs[0], dict):
                    # List of dicts with 'recommendation' key
                    recommendations = [r.get('recommendation', str(r)) for r in recs]
                else:
                    # List of strings
                    recommendations = [str(r) for r in recs]
        
        return StandardResponse(
            response_type=ResponseType.ANALYSIS,
            message=f"Analysis of: {query}",
            data=data,
            insights=insights,
            metrics=metrics,
            visualization=visualization,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        _logger.error(f"Error formatting analysis response: {e}")
        return StandardResponse(
            response_type=ResponseType.ERROR,
            message=f"Error formatting analysis: {str(e)}",
            error=str(e)
        )

def format_raw_data_response(data: Dict[str, Any], query: str) -> StandardResponse:
    """Format raw data response."""
    return StandardResponse(
        response_type=ResponseType.RAW_DATA,
        message=f"Retrieved data for: {query}",
        data=data,
        timestamp=datetime.now().isoformat()
    )

def format_metadata_response(data: Dict[str, Any], query: str) -> StandardResponse:
    """Format metadata response."""
    return StandardResponse(
        response_type=ResponseType.METADATA,
        message=f"Metadata for: {query}",
        data=data,
        timestamp=datetime.now().isoformat()
    )

def convert_metrics_to_standard(metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert various metric formats to standard format."""
    standard_metrics = []
    
    try:
        if isinstance(metrics_data, dict):
            # Handle different metric formats
            for key, value in metrics_data.items():
                if isinstance(value, (int, float, str)):
                    standard_metrics.append({
                        "title": key.replace('_', ' ').title(),
                        "value": str(value),
                        "description": f"{key} metric"
                    })
                elif isinstance(value, dict):
                    # Nested metrics
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (int, float, str)):
                            standard_metrics.append({
                                "title": f"{key} {sub_key}".replace('_', ' ').title(),
                                "value": str(sub_value),
                                "description": f"{key}.{sub_key}"
                            })
        
        return standard_metrics[:10]  # Limit to 10 metrics
        
    except Exception as e:
        _logger.error(f"Error converting metrics: {e}")
        return []

def create_sub_agents():
    """Create and return all sub-agents with proper configurations."""
    global MCP_SERVERS, MODEL_CONFIG
    
    # Ensure configurations are loaded
    if MCP_SERVERS is None or MODEL_CONFIG is None:
        MCP_SERVERS, MODEL_CONFIG = initialize_configurations()
    
    # Create retrieval agent
    retrieval_agent = get_retrieval_agent(
        mcp_servers=MCP_SERVERS,
        model_config=MODEL_CONFIG
    )
    
    return retrieval_agent

def get_root_agent() -> LlmAgent:
    """Create and configure the root orchestrator agent."""
    if MODEL_CONFIG["type"] == "deepseek":
        model_instance = LiteLlm(
            model="deepseek/deepseek-chat",
            api_key=MODEL_CONFIG.get("api_key")
        )
    else:
        model_instance = LiteLlm(
            model=MODEL_CONFIG.get("model", "gemini-2.0-flash-exp"),
            api_base=MODEL_CONFIG.get("api_base"),
            api_key=MODEL_CONFIG.get("api_key", "EMPTY")
        )
    
    # Create sub-agents
    retrieval_agent = create_sub_agents()
    
    # Create AgentTools for the orchestrator to use
    retrieval_tool = AgentTool(agent=retrieval_agent)
    
    # Create the root agent with after_tool_callback
    agent = LlmAgent(
        name="data_science_orchestrator",
        model=model_instance,
        instruction=get_root_instruction(),
        description="Orchestrates data retrieval and analysis workflows",
        tools=[retrieval_tool],
        sub_agents=[retrieval_agent],
        before_agent_callback=root_before_callback,
        after_tool_callback=root_after_tool_callback,
        generate_content_config=types.GenerateContentConfig(
            temperature=0.1,
            top_p=0.95,
            max_output_tokens=4096
        )
    )
    
    _logger.info("=" * 60)
    _logger.info("Data Science Agent System Initialized")
    _logger.info(f"Root Agent: {agent.name}")
    _logger.info(f"Sub-agents: {[a.name for a in agent.sub_agents]}")
    _logger.info(f"Tools: {[t.name for t in agent.tools]}")
    _logger.info(f"MCP Servers: {len(MCP_SERVERS) if MCP_SERVERS else 0}")
    _logger.info("=" * 60)
    
    return agent

# Initialize configurations early
initialize_configurations()

# Create the root agent instance for export
root_agent = get_root_agent()