# analytics_schema.py - Simplified schema for analytics agent
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class VisualizationSchema(BaseModel):
    """Simplified visualization schema."""
    type: str = Field(description="Chart type: bar_chart, line_chart, pie_chart, scatter_plot, table")
    title: str = Field(description="Chart title")
    x_field: Optional[str] = Field(default=None, description="X-axis field name")
    y_field: Optional[str] = Field(default=None, description="Y-axis field name")
    data: List[Dict[str, Any]] = Field(description="Chart data as list of objects")


class MetricSchema(BaseModel):
    """Simplified metric schema."""
    title: str = Field(description="Metric title")
    value: str = Field(description="Metric value as string")
    description: Optional[str] = Field(default=None, description="Optional description")


class AnalyticsResponseSchema(BaseModel):
    """Simplified analytics response schema that works with OpenAI."""
    response_type: str = Field(description="Response type: analysis, raw_data, error")
    message: str = Field(description="Human-readable message")
    
    # Simple nested object instead of complex structure
    insights: List[str] = Field(description="List of insights")
    summary: str = Field(description="Overall summary")
    
    # Optional visualization - make it simpler
    visualization: Optional[VisualizationSchema] = Field(default=None, description="Visualization configuration")
    
    # Optional metrics - keep it simple
    metrics: Optional[List[MetricSchema]] = Field(default=None, description="Key metrics")
    
    # Raw data if needed
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="Original data")
    
    class Config:
        schema_extra = {
            "example": {
                "response_type": "analysis",
                "message": "Monthly sales analysis",
                "insights": ["Sales peak in December", "Q2 shows growth"],
                "summary": "Positive year-over-year trend",
                "visualization": {
                    "type": "line_chart",
                    "title": "Monthly Sales",
                    "x_field": "month",
                    "y_field": "sales",
                    "data": [
                        {"month": "Jan", "sales": 10000},
                        {"month": "Feb", "sales": 12000}
                    ]
                },
                "metrics": [
                    {"title": "Total Revenue", "value": "120000", "description": "Year to date"}
                ]
            }
        }