"""Shared utilities, MCP tools, and model configuration."""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.adk.models.lite_llm import LiteLlm

_logger = logging.getLogger(__name__)

def load_mcp_config() -> List[Dict[str, Any]]:
    """Load MCP servers configuration from environment."""
    mcp_env = os.getenv("MCP_SERVERS_JSON")
    if not mcp_env:
        _logger.warning("MCP_SERVERS_JSON is not defined - MCP tools will not be available")
        return []
    
    try:
        servers = json.loads(mcp_env)
        if not isinstance(servers, list):
            _logger.error("MCP_SERVERS_JSON must be a list")
            return []
        
        _logger.info(f"Loaded {len(servers)} MCP server configurations")
        return servers
        
    except json.JSONDecodeError as e:
        _logger.error(f"Failed to parse MCP_SERVERS_JSON: {e}")
        return []

def get_model_config() -> Dict[str, Any]:
    """Get the model configuration based on environment variables."""
    model_type = os.getenv("MODEL_TYPE", "vllm").lower()
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if model_type == "deepseek" or deepseek_api_key:
        _logger.info("Using DeepSeek model")
        return {
            "type": "deepseek",
            "model": "deepseek/deepseek-chat",
            "api_key": deepseek_api_key,
            "name": "deepseek_agent"
        }
    else:
        _logger.info(f"Using vLLM model: {os.getenv('VLLM_MODEL_NAME', 'openai/mistral-large:123b')}")
        return {
            "type": "vllm",
            "model": os.getenv("VLLM_MODEL_NAME", "openai/mistral-large:123b"),
            "api_base": os.getenv("VLLM_BASE_URL", "http://localhost:9000/v1"),
            "api_key": os.getenv("VLLM_API_KEY", "EMPTY"),
            "name": "vllm_agent"
        }

def create_mcp_toolsets(servers: List[Dict[str, Any]]) -> List[McpToolset]:
    """
    Create MCP toolsets from server configurations.
    
    Args:
        servers: List of MCP server configurations
        
    Returns:
        List of McpToolset instances
    """
    toolsets = []
    
    for server in servers:
        try:
            url = server.get("url")
            requires_auth = server.get("auth", False)
            
            if not url:
                _logger.error("MCP server entry missing 'url'")
                continue
            
            headers = None
            if requires_auth:
                mcp_auth_token = os.getenv("MCP_AUTH_TOKEN")
                mcp_auth_scheme = os.getenv("MCP_AUTH_SCHEME", "Bearer")
                
                if not mcp_auth_token:
                    _logger.error(f"MCP server {url} requires auth, but MCP_AUTH_TOKEN is not set")
                    continue
                
                headers = {
                    "Authorization": f"{mcp_auth_scheme} {mcp_auth_token}"
                }
            
            toolset = McpToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=url,
                    headers=headers
                )
            )
            toolsets.append(toolset)
            _logger.info(f"Created MCP toolset for: {url}")
            
        except Exception as e:
            _logger.error(f"Failed to create MCP toolset: {e}")
    
    return toolsets

def get_lite_llm_model(model_config: Dict[str, Any]) -> LiteLlm:
    """Create a LiteLlm instance from model configuration."""
    if model_config["type"] == "deepseek":
        return LiteLlm(
            model=model_config["model"],
            api_key=model_config["api_key"]
        )
    else:
        return LiteLlm(
            model=model_config["model"],
            api_base=model_config.get("api_base"),
            api_key=model_config.get("api_key", "EMPTY")
        )