# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This file initializes a FastAPI application for Data Science agent
using get_fast_api_app() from ADK. Session service URI and a flag
for a web interface configured via environment variables.
It can then be run using Uvicorn, which listens on a port specified by
the PORT environment variable or defaults to 8080.
This approach offers more flexibility, particularly if you want to
embed Data Science agent within a custom FastAPI application.
It is used for Cloud Run deployment with standard gcloud run deploy command.
"""

import os
import logging
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Get session service URI from environment variables
session_uri = os.getenv("SESSION_SERVICE_URI", None)

# Get Enable Web interface serving flag from environment variables
# Set web=True if you intend to serve a web interface, False otherwise
web_interface_enabled = os.getenv("SERVE_WEB_INTERFACE", 'False').lower() in ('true', '1')

# Prepare arguments for get_fast_api_app
app_args = {"agents_dir": AGENT_DIR, "web": web_interface_enabled}

# Only include session_service_uri if it's provided
if session_uri:
    app_args["session_service_uri"] = session_uri
else:
    logger.warning(
        "SESSION_SERVICE_URI not provided. Using in-memory session service instead. "
        "All sessions will be lost when the server restarts."
    )

# Create FastAPI app with appropriate arguments
app: FastAPI = get_fast_api_app(**app_args)

app.title = "data_science"
app.description = "Data Science Agent System"

if __name__ == "__main__":
    # Display agent information when starting
    try:
        # Try to import and display agent info
        from data_science.agent import root_agent
        
        print("=" * 70)
        print("DATA SCIENCE AGENT SYSTEM")
        print("=" * 70)
        print(f"Root Agent: {root_agent.name}")
        print(f"Description: {root_agent.description}")
        
        # Display sub-agents if available
        if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
            print(f"Sub-agents: {[a.name for a in root_agent.sub_agents]}")
        
        # Display tools if available
        if hasattr(root_agent, 'tools') and root_agent.tools:
            print(f"Tools available: {[t.name for t in root_agent.tools]}")
        
        print("=" * 70)
        print("\nStarting FastAPI server...")
        print("Agent available via ADK web server:")
        print("  adk web --agent-module data_science.agent:root_agent")
        print("\nExample queries:")
        print("  • 'Get sales data from last quarter'")
        print("  • 'Analyze customer trends over time'")
        print("  • 'Create a bar chart of monthly revenue'")
        print("  • 'Generate a report on product performance'")
        print("=" * 70)
        
    except ImportError as e:
        print(f"Warning: Could not import agent details - {e}")
        print("Starting FastAPI server without agent info display...")
    
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    port = int(os.environ.get("PORT", 8080))
    print(f"\nStarting server on http://0.0.0.0:{port}")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)