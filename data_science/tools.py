"""Shared utilities, MCP tools, and model configuration."""

import os
import json
import logging
import requests
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

def test_mcp_connection(
    url: str,
    *,
    requires_auth: bool = False,
    auth_token: Optional[str] = None,
    auth_scheme: str = "Bearer",
    timeout: int = 3,
) -> bool:
    """
    Test MCP server connectivity.

    Returns True if server is reachable, False if not.
    """
    payload = {"jsonrpc": "2.0"}  # minimal JSON-RPC message

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json,text/event-stream",
    }

    if requires_auth:
        if not auth_token:
            _logger.error("MCP auth required but token missing")
            return False
        headers["Authorization"] = f"{auth_scheme} {auth_token}"

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
            stream=True,  # important for streamable HTTP
        )

        # Any response <500 is considered reachable
        if response.status_code >= 500:
            _logger.error(
                "MCP server %s returned server error: %s",
                url,
                response.status_code,
            )
            return False

        _logger.info("MCP server reachable: %s (status=%s)", url, response.status_code)
        return True

    except requests.exceptions.RequestException as exc:
        _logger.error("MCP connection failed for %s: %s", url, exc)
        return False


def create_mcp_toolsets(servers: List[Dict[str, Any]]) -> List[McpToolset]:
    toolsets = []

    for server in servers:
        url = server.get("url")
        if not url:
            _logger.error("MCP server entry missing 'url'")
            continue

        requires_auth = server.get("auth", False)
        token = os.getenv("MCP_AUTH_TOKEN")
        scheme = os.getenv("MCP_AUTH_SCHEME", "Bearer")

        # Test connection
        if not test_mcp_connection(
            url,
            requires_auth=requires_auth,
            auth_token=token,
            auth_scheme=scheme,
        ):
            continue

        headers = None
        if requires_auth:
            headers = {"Authorization": f"{scheme} {token}"}

        try:
            toolsets.append(
                McpToolset(
                    connection_params=StreamableHTTPConnectionParams(
                        url=url,
                        headers=headers
                    )
                )
            )
            _logger.info(f"Created MCP toolset for: {url}")
        except Exception as e:
            _logger.error(f"Failed to create MCP toolset for {url}: {e}")

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

