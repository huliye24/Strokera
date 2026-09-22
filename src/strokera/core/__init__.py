"""
Core data structures for Strokera.

This module contains the fundamental data structures:
- Stroke: Single brush stroke representation
- StrokeGraph: Graph of strokes for the complete painting
- Brush: Brush type and physics parameters
- BrushEngine: Renders strokes to images
- Canvas: The drawing surface with layers
- Pigment: Color and material definitions
"""

from strokera.core.stroke import Stroke, StrokeType, StrokeGraph
from strokera.core.brush import Brush, BrushType, BrushPhysics, BrushEngine
from strokera.core.canvas import Canvas, Layer, LayerType, BlendMode, Surface, CanvasState
from strokera.core.pigment import Pigment, PigmentSet

__all__ = [
    # Stroke
    "Stroke",
    "StrokeType", 
    "StrokeGraph",
    # Brush
    "Brush",
    "BrushType",
    "BrushPhysics",
    "BrushEngine",
    # Canvas
    "Canvas",
    "Layer",
    "LayerType",
    "BlendMode",
    "Surface",
    "CanvasState",
    # Pigment
    "Pigment",
    "PigmentSet",
]
