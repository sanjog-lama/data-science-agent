"""Root Orchestrator Agent for Data Science System - Following ADK Patterns."""

import logging
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
from .sub_agents.analytics.agent import get_analytics_agent

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

def root_before_callback(callback_context: CallbackContext) -> None:
    """
    Root agent callback: Extract user query and store in session state.
    """
    try:
        # The user message is in user_content, NOT current_message
        user_content = callback_context.user_content
        
        if user_content and hasattr(user_content, 'parts') and user_content.parts:
            # Get the text from the first part
            user_query = user_content.parts[0].text
            _logger.info(f"Root agent extracted query: '{user_query[:80]}...'")
        else:
            user_query = "Unknown query"
            _logger.warning("Could not extract user query from user_content")
        
        # Store in session state for ALL sub-agents to access
        callback_context.state['original_user_query'] = user_query
        callback_context.state['current_query'] = user_query
        
        _logger.info(f"Root agent stored query in state: {user_query}")
        
    except Exception as e:
        _logger.error(f"Error in root_before_callback: {e}")

def create_sub_agents() -> tuple:
    """Create and return all sub-agents with proper configurations."""
    global MCP_SERVERS, MODEL_CONFIG
    
    # Ensure configurations are loaded
    if MCP_SERVERS is None or MODEL_CONFIG is None:
        MCP_SERVERS, MODEL_CONFIG = initialize_configurations()
    
    # Create retrieval agent with MCP tools
    retrieval_agent = get_retrieval_agent(
        mcp_servers=MCP_SERVERS,
        model_config=MODEL_CONFIG
    )
    
    # Create analytics agent
    analytics_agent = get_analytics_agent(
        model_config=MODEL_CONFIG
    )
    
    return retrieval_agent, analytics_agent

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
    retrieval_agent, analytics_agent = create_sub_agents()
    
    # Create AgentTools for the orchestrator to use
    retrieval_tool = AgentTool(
        agent=retrieval_agent,
    )
    
    analytics_tool = AgentTool(
        agent=analytics_agent,
    )
    
    # Create the root agent
    agent = LlmAgent(
        name="data_science_orchestrator",
        model=model_instance,
        instruction=get_root_instruction(),
        description="Orchestrates data retrieval and analysis workflows",
        tools=[retrieval_tool, analytics_tool],
        sub_agents=[retrieval_agent, analytics_agent],
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
    _logger.info(f"MCP Servers: {len(MCP_SERVERS) if MCP_SERVERS else 0}")
    _logger.info("=" * 60)
    
    return agent

# Initialize configurations early
initialize_configurations()

# Create the root agent instance for export
root_agent = get_root_agent()