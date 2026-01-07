"""Analytics and Visualization Agent (CHART-FIRST, NO TEXT)."""

import json
import logging
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.genai import types

from data_science.tools import get_lite_llm_model
from .prompts import get_analytics_instruction

def get_analytics_agent(model_config: Dict[str, Any]) -> LlmAgent:
    """Create the analytics and visualization agent (chart-only)."""

    model = get_lite_llm_model(model_config)
    
    agent = LlmAgent(
        name="analytics_agent",
        model=model,
        instruction=get_analytics_instruction(),
        description="Creates structured chart specifications for UI rendering",
        output_key="analytics_output",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=4096
        ),
    )

    return agent
