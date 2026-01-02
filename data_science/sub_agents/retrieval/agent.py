"""Data Retrieval Agent with structured output schema."""

import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum as PyEnum
from pydantic import BaseModel, Field, field_validator
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from .prompts import get_retrieval_instruction

_logger = logging.getLogger(__name__)


class DataSourceEnum(str, PyEnum):
    """Available data sources."""
    POSTGRESQL = "postgresql"
    MSSQL = "mssql"
    HUBSPOT = "hubspot"
    OPENMETADATA = "openmetadata"
    UNKNOWN = "unknown"


class DataTypeEnum(str, PyEnum):
    """Type of data retrieved."""
    TABLE = "table"
    JSON = "json"
    METADATA = "metadata"
    TEXT = "text"


class RetrievalResponse(BaseModel):
    """Standardized retrieval response schema."""
    
    data_source: str = Field(
        description="The data source used for retrieval"
    )
    
    data_type: str = Field(
        description="Type of data structure returned"
    )
    
    summary: str = Field(
        description="Brief summary of what data was retrieved (1-2 sentences)"
    )
    
    data: Dict[str, Any] = Field(
        description="The actual retrieved data in structured format"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the retrieval (row count, columns, etc.)"
    )
    
    needs_visualization: bool = Field(
        default=False,
        description="Whether the data would benefit from visualization"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if retrieval failed"
    )
    
    @field_validator('data_source')
    @classmethod
    def validate_data_source(cls, v):
        """Validate data_source field."""
        valid_sources = [ds.value for ds in DataSourceEnum]
        if v not in valid_sources:
            return "unknown"
        return v
    
    @field_validator('data_type')
    @classmethod
    def validate_data_type(cls, v):
        """Validate data_type field."""
        valid_types = [dt.value for dt in DataTypeEnum]
        if v not in valid_types:
            return "text"
        return v


def get_retrieval_agent(mcp_servers: List[Dict[str, Any]], 
                       model_config: Dict[str, Any]) -> Agent:
    """Create the data retrieval agent with structured output."""
    
    from ...tools import create_mcp_toolsets, get_lite_llm_model
    
    # Create MCP toolsets
    mcp_toolsets = create_mcp_toolsets(mcp_servers)
    
    # Create model instance
    model = get_lite_llm_model(model_config)
    
    agent = Agent(
        name="data_retrieval_agent",
        model=model,
        instruction=get_retrieval_instruction(),
        description="Retrieves data from PostgreSQL, MSSQL, HubSpot, and metadata systems via MCP",
        tools=mcp_toolsets,
        output_schema=RetrievalResponse,
        output_key="retrieval_response",
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
            
    except Exception as e:
        _logger.error(f"Error in retrieval_before_callback: {e}")


def retrieval_after_tool_callback(tool, args, tool_context, tool_response):
    """Store retrieval results in state for potential use by analytics agent."""
    try:
        if tool_response:
            # Store raw tool response for analytics agent if needed
            tool_context.state['raw_tool_response'] = tool_response
            _logger.info("Raw tool response stored in state")
            
    except Exception as e:
        _logger.error(f"Error in retrieval_after_tool_callback: {e}")

    return None