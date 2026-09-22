"""
Planning module - Image analysis, painting planning, and stroke prediction.

This module implements the "planning" layer of Strokera:
- ImageAnalyzer: Semantic understanding of input images
- PaintingPlanner: Layer and region structure planning
- StrokePlanner: Stroke prediction and generation

Based on architectures from:
- Paint-Anything (semantic segmentation)
- PaintTransformer (stroke prediction)
- LearningToPaint (progressive rendering)
"""

from strokera.planning.image_analyzer import (
    ImageAnalyzer,
    AnalysisResult,
    AnalysisMode,
    Segment,
)
from strokera.planning.painting_planner import (
    PaintingPlanner,
    PaintingPlan,
    PaintLayer,
    PaintLayerType,
    PaintRegion,
)
from strokera.planning.stroke_planner import (
    StrokePlanner,
    StrokeGraph,
    StrokePredictionModel,
    StrokeGenerator,
)

__all__ = [
    # Image Analyzer
    "ImageAnalyzer",
    "AnalysisResult",
    "AnalysisMode",
    "Segment",
    # Painting Planner
    "PaintingPlanner",
    "PaintingPlan",
    "PaintLayer",
    "PaintLayerType",
    "PaintRegion",
    # Stroke Planner
    "StrokePlanner",
    "StrokePredictionModel",
    "StrokeGenerator",
]
