"""Analytics Agent - Consumes retrieval_response and outputs structured analysis."""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum as PyEnum
from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from .prompts import get_analytics_instruction

_logger = logging.getLogger(__name__)


class ChartTypeEnum(str, PyEnum):
    """Supported chart types for visualization."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"
    SUMMARY = "summary"


class AnalysisResponse(BaseModel):
    """Structured output schema for analytics agent."""
    
    analysis_summary: str = Field(
        description="Brief summary of insights from the retrieved data"
    )
    
    chart_recommendations: List[str] = Field(
        description="Recommended chart types for visualization",
        default_factory=list
    )
    
    computed_metrics: Optional[Dict[str, Any]] = Field(
        description="Optional key metrics or aggregated values",
        default_factory=dict
    )
    
    visualizations: Optional[List[Dict[str, Any]]] = Field(
        description="Optional list of charts or table data ready for frontend visualization",
        default_factory=list
    )
    
    disclaimer: str = Field(
        description="Disclaimer about analysis",
        default="This analysis is automatically generated. Please verify before critical decisions."
    )


def analytics_before_callback(callback_context: CallbackContext) -> None:
    """
    Pull the retrieval response from state and store locally for analytics.
    """
    try:
        retrieval_data = callback_context.state.get('retrieval_response')
        if not retrieval_data:
            _logger.warning("No retrieval_response found in state for analytics agent.")
            callback_context.state['analytics_input'] = None
            return

        _logger.info("Analytics agent received retrieval data from state.")
        callback_context.state['analytics_input'] = retrieval_data

    except Exception as e:
        _logger.exception(f"Error in analytics_before_callback: {e}")


def get_analytics_agent(model_config: Dict[str, Any]) -> Agent:
    """
    Create analytics agent which consumes retrieval_response and outputs structured analysis.
    """
    from ...tools import get_lite_llm_model

    # Create model instance
    model = get_lite_llm_model(model_config)

    agent = Agent(
        name="analytics_agent",
        model=model,
        instruction=get_analytics_instruction(),
        description="Analyzes retrieved data and outputs structured insights and visualizations",
        tools=[],
        output_schema=AnalysisResponse,
        output_key="analytics_response",
        before_agent_callback=analytics_before_callback
    )

    return agent