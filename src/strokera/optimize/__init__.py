"""
Optimization module - Stroke parameter optimization using differentiable rendering.

This module provides:
- DifferentiableRenderer: Wrapper for diffvg
- StrokeOptimizer: Gradient-based optimization
- GradientDescentOptimizer: Simple optimization fallback

The optimizer adjusts stroke parameters (position, width, color, path)
to minimize the difference between rendered output and target image.
"""

from strokera.optimize.stroke_optimizer import (
    StrokeOptimizer,
    GradientDescentOptimizer,
    DifferentiableRenderer,
    OptimizationConfig,
    OptimizationResult,
)

__all__ = [
    "StrokeOptimizer",
    "GradientDescentOptimizer", 
    "DifferentiableRenderer",
    "OptimizationConfig",
    "OptimizationResult",
]
