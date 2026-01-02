# standard_response.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from enum import Enum


class ResponseType(str, Enum):
    RAW_DATA = "raw_data"
    ANALYSIS = "analysis"
    ERROR = "error"
    METADATA = "metadata"


class VisualizationType(str, Enum):
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    TABLE = "table"
    METRIC_CARDS = "metric_cards"


class StandardResponse(BaseModel):
    """Standardized response format for UI rendering."""
    
    # Core fields (always present)
    response_type: ResponseType = Field(description="Type of response")
    message: str = Field(description="Human-readable message")
    timestamp: Optional[str] = Field(default=None, description="Response timestamp")
    
    # Data fields (conditional)
    data: Optional[Dict[str, Any]] = Field(default=None, description="Raw data or analysis results")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    # Visualization fields (only for analysis type)
    visualization: Optional[Dict[str, Any]] = Field(default=None, description="Visualization configuration")
    metrics: Optional[List[Dict[str, Any]]] = Field(default=None, description="Key metrics")
    
    # Standardized insight fields
    insights: Optional[List[str]] = Field(default=None, description="Key insights as strings")
    recommendations: Optional[List[str]] = Field(default=None, description="Business recommendations")
    
    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "response_type": "raw_data",
                    "message": "Retrieved customer data",
                    "data": {
                        "rows": [...],
                        "columns": ["id", "name", "email"],
                        "count": 100
                    }
                },
                {
                    "response_type": "analysis",
                    "message": "Sales trend analysis",
                    "insights": ["Sales increased by 20%", "Q1 was strongest quarter"],
                    "metrics": [
                        {"title": "Total Sales", "value": "$100,000", "description": "Quarterly total"},
                        {"title": "Growth", "value": "20%", "description": "Quarter over quarter"}
                    ],
                    "visualization": {
                        "type": "line_chart",
                        "title": "Quarterly Sales Trend",
                        "x_field": "quarter",
                        "y_field": "sales",
                        "data": [...]
                    }
                },
                {
                    "response_type": "metadata",
                    "message": "Database schema information",
                    "data": {
                        "tables": ["customers", "orders", "products"],
                        "count": 3
                    }
                }
            ]
        }