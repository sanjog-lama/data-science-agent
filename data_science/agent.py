"""Root Orchestrator Agent for Data Science System - Following ADK Patterns."""

import os
import json
import logging
from typing import Dict, Any, Optional
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
# from .sub_agents.analytics.agent import get_analytics_agent


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

def determine_query_type(query: str) -> str:
    """Determine if query needs retrieval, analysis, or both."""
    query_lower = query.lower()
    
    analysis_keywords = [
        'analyze', 'analysis', 'trend', 'pattern', 'insight',
        'visualize', 'chart', 'graph', 'plot', 'compare',
        'correlation', 'statistic', 'average',
        'insight', 'identify',
        'relationship', 'predict', 'forecast'
    ]
    
    retrieval_keywords = [
        'list', 'show', 'get', 'fetch', 'retrieve', 'data',
        'tables', 'schema', 'metadata', 'records', 'rows',
        'columns', 'structure', 'describe'
    ]
    
    has_analysis = any(keyword in query_lower for keyword in analysis_keywords)
    has_retrieval = any(keyword in query_lower for keyword in retrieval_keywords)
    
    if has_analysis and has_retrieval:
        return "analysis"  # If both, prioritize analysis
    elif has_analysis:
        return "analysis"
    elif has_retrieval:
        return "retrieval"
    else:
        # For ambiguous queries, check context
        if any(word in query_lower for word in ['data', 'table', 'database', 'sales', 'customer']):
            return "retrieval"  # Data-related but no clear analysis keyword
        else:
            return "analysis"  # Default to analysis for general questions

def root_before_callback(callback_context: CallbackContext) -> None:
    """
    Root agent callback: Extract user query and determine flow.
    """
    try:
        # Extract user query
        user_content = callback_context.user_content
        user_query = extract_query_from_content(user_content)
        
        if user_query:
            _logger.info(f"Root agent extracted query: '{user_query[:80]}...'")
            
            # Determine query type
            query_type = determine_query_type(user_query)
            _logger.info(f"Determined query type: {query_type}")
            
            # Store in session state for ALL sub-agents to access
            callback_context.state['original_user_query'] = user_query
            callback_context.state['current_query'] = user_query
            callback_context.state['query_type'] = query_type
            # callback_context.state['query_processed'] = False
            # callback_context.state['retrieval_completed'] = False
            
            # Also store metadata
            callback_context.state['query_timestamp'] = os.path.getmtime(__file__)
            
            _logger.info(f"Root agent stored query in state. Type: {query_type}")
        else:
            user_query = "Unknown query"
            _logger.warning("Could not extract user query from user_content")
            # callback_context.state['original_user_query'] = user_query
            # callback_context.state['query_type'] = "retrieval"  # Default
        
    except Exception as e:
        _logger.error(f"Error in root_before_callback: {e}")
        # callback_context.state['original_user_query'] = "Error extracting query"
        # callback_context.state['query_type'] = "retrieval"


def create_sub_agents() -> tuple:
    """Create and return all sub-agents with proper configurations."""
    global MCP_SERVERS, MODEL_CONFIG
    
    # Ensure configurations are loaded
    if MCP_SERVERS is None or MODEL_CONFIG is None:
        MCP_SERVERS, MODEL_CONFIG = initialize_configurations()
    
    # Create retrieval agent with MCP tools and structured output
    retrieval_agent = get_retrieval_agent(
        mcp_servers=MCP_SERVERS,
        model_config=MODEL_CONFIG
    )

    # analytics_agent = get_analytics_agent(
    #     model_config=MODEL_CONFIG
    # )
    
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
    # analytics_tool = AgentTool(agent=analytics_agent)
    
    # Create the root agent with error handling
    agent = LlmAgent(
        name="data_science_orchestrator",
        model=model_instance,
        instruction=get_root_instruction(),
        description="Orchestrates data retrieval and analysis workflows",
        # tools=[retrieval_tool, analytics_tool],
        tools=[retrieval_tool],
        # sub_agents=[retrieval_agent, analytics_agent],
        sub_agents=[retrieval_agent],
        before_agent_callback=root_before_callback,
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