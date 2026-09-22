"""
Stroke Planner - Predicts stroke parameters based on painting plan.

Based on PaintTransformer architecture: takes a region and predicts
what strokes should be placed where with what parameters.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any, Callable
import numpy as np
from numpy.typing import NDArray

from strokera.core.stroke import Stroke, StrokeType, StrokeGraph
from strokera.core.brush import Brush
from strokera.planning.painting_planner import PaintingPlan, PaintRegion, PaintLayer


class StrokePredictionModel:
    """
    Neural network model for stroke prediction.
    
    This is a placeholder for the actual model.
    In v0.1, we'll use heuristic-based stroke generation.
    In future versions, this will wrap PaintTransformer or similar.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the model."""
        self.model_path = model_path
        self._model = None
        self._device = "cpu"
    
    def predict(self, target_image: NDArray[np.uint8],
                region: PaintRegion,
                num_strokes: int) -> List[Dict[str, Any]]:
        """
        Predict strokes for a region.
        
        Args:
            target_image: Target region image
            region: PaintRegion with properties
            num_strokes: Number of strokes to predict
            
        Returns:
            List of stroke parameter dicts
        """
        # In v0.1, use heuristic generation
        return self._heuristic_stroke_generation(target_image, region, num_strokes)
    
    def _heuristic_stroke_generation(self, image: NDArray[np.uint8],
                                     region: PaintRegion,
                                     num_strokes: int) -> List[Dict[str, Any]]:
        """Generate strokes using heuristics."""
        h, w = image.shape[:2] if len(image.shape) == 3 else image.shape
        
        if h == 0 or w == 0:
            return []
        
        strokes = []
        
        # Calculate stroke spacing
        area = h * w
        spacing = np.sqrt(area / num_strokes) if num_strokes > 0 else 10
        
        # Generate grid of stroke centers
        for i in range(num_strokes):
            # Random offset from grid
            grid_x = (i % int(np.sqrt(num_strokes * w / h))) * spacing
            grid_y = (i // int(np.sqrt(num_strokes * w / h))) * spacing
            
            # Add randomness
            offset_x = np.random.uniform(-spacing/3, spacing/3)
            offset_y = np.random.uniform(-spacing/3, spacing/3)
            
            x = np.clip(grid_x + offset_x, 0, w - 1)
            y = np.clip(grid_y + offset_y, 0, h - 1)
            
            # Sample color at position
            if len(image.shape) == 3:
                color = tuple(image[int(y), int(x), :3].astype(float) / 255.0)
            else:
                gray = image[int(y), int(x)] / 255.0
                color = (gray, gray, gray)
            
            # Generate stroke parameters
            stroke_params = {
                "x": x,
                "y": y,
                "width": region.stroke_width_base * np.random.uniform(
                    1 - region.stroke_width_variance,
                    1 + region.stroke_width_variance
                ),
                "color": color,
                "angle": np.random.uniform(0, np.pi * 2),
                "length": spacing * np.random.uniform(0.5, 2.0),
            }
            
            strokes.append(stroke_params)
        
        return strokes


@dataclass
class StrokeGenerator:
    """
    Generates strokes for a paint region.
    
    Responsible for converting a region's properties into
    actual stroke objects.
    """
    
    generator_type: str = "heuristic"  # heuristic, neural, hybrid
    
    def generate_strokes(self, region: PaintRegion,
                        canvas_size: Tuple[int, int],
                        brush: Brush,
                        num_strokes: int) -> List[Stroke]:
        """
        Generate strokes for a region.
        
        Args:
            region: The paint region
            canvas_size: (width, height) of the canvas
            brush: Brush to use
            num_strokes: Target number of strokes
            
        Returns:
            List of Stroke objects
        """
        # Create strokes based on region properties
        strokes = []
        width, height = canvas_size
        
        x_min, y_min, w, h = region.bbox
        region_x = int(x_min * width)
        region_y = int(y_min * height)
        region_w = int(w * width)
        region_h = int(h * height)
        
        # Generate stroke grid
        grid_cols = int(np.ceil(np.sqrt(num_strokes * region_w / region_h)))
        grid_rows = int(np.ceil(num_strokes / grid_cols))
        
        spacing_x = region_w / grid_cols if grid_cols > 0 else 1
        spacing_y = region_h / grid_rows if grid_rows > 0 else 1
        
        stroke_idx = 0
        for row in range(grid_rows):
            for col in range(grid_cols):
                if stroke_idx >= num_strokes:
                    break
                    
                # Calculate stroke center
                cx = region_x + (col + 0.5) * spacing_x
                cy = region_y + (row + 0.5) * spacing_y
                
                # Add some randomness
                cx += np.random.uniform(-spacing_x * 0.3, spacing_x * 0.3)
                cy += np.random.uniform(-spacing_y * 0.3, spacing_y * 0.3)
                
                # Create stroke
                stroke = self._create_stroke(
                    center=(cx, cy),
                    color=region.target_color,
                    width=region.stroke_width_base,
                    angle=np.random.uniform(0, np.pi * 2),
                    brush=brush,
                    region=region,
                )
                
                strokes.append(stroke)
                stroke_idx += 1
                
            if stroke_idx >= num_strokes:
                break
        
        return strokes
    
    def _create_stroke(self, center: Tuple[float, float],
                      color: Tuple[float, float, float],
                      width: float,
                      angle: float,
                      brush: Brush,
                      region: PaintRegion) -> Stroke:
        """Create a single stroke with Bezier path."""
        # Calculate stroke length and shape
        length = width * 3
        half_length = length / 2
        
        # Direction vector
        dx = np.cos(angle) * half_length
        dy = np.sin(angle) * half_length
        
        # Control points for Bezier curve
        p0 = (center[0] - dx, center[1] - dy)
        p1 = (center[0] - dx * 0.5, center[1] - dy * 0.5)
        p2 = (center[0] + dx * 0.5, center[1] + dy * 0.5)
        p3 = (center[0] + dx, center[1] + dy)
        
        # Sample points along Bezier curve
        num_samples = 10
        path = []
        for i in range(num_samples):
            t = i / (num_samples - 1) if num_samples > 1 else 0
            
            # Cubic Bezier
            mt = 1 - t
            x = mt**3 * p0[0] + 3*mt**2*t * p1[0] + 3*mt*t**2 * p2[0] + t**3 * p3[0]
            y = mt**3 * p0[1] + 3*mt**2*t * p1[1] + 3*mt*t**2 * p2[1] + t**3 * p3[1]
            path.append((x, y))
        
        # Create stroke
        stroke = Stroke(
            type=StrokeType.PREDICTED,
            layer_id=region.segment_id or "default",
            brush_id=brush.id,
            path=path,
            width=width,
            color=color,
            opacity=0.8,
            angle=angle,
        )
        
        # Set taper profile
        if brush.taper_enabled:
            num_pts = len(path)
            profile = np.zeros(num_pts, dtype=np.float32)
            for i in range(num_pts):
                t = i / (num_pts - 1) if num_pts > 1 else 0
                # Taper at both ends
                if t < brush.taper_start:
                    profile[i] = t / brush.taper_start
                elif t > 1 - brush.taper_end:
                    profile[i] = (1 - t) / brush.taper_end
                else:
                    profile[i] = 1.0
            stroke.width_profile = profile
            
        return stroke


class StrokePlanner:
    """
    Plans strokes based on painting plan.
    
    Coordinates stroke generation across all regions and layers,
    producing a complete StrokeGraph.
    
    Based on the PaintTransformer architecture.
    """
    
    def __init__(self, model: Optional[StrokePredictionModel] = None):
        """
        Initialize the stroke planner.
        
        Args:
            model: Optional neural model for stroke prediction
        """
        self.model = model or StrokePredictionModel()
        self.generator = StrokeGenerator()
    
    def plan(self, plan: PaintingPlan,
             brush: Optional[Brush] = None,
             progress_callback: Optional[Callable[[int, int, str], None]] = None) -> StrokeGraph:
        """
        Generate strokes for the entire painting plan.
        
        Args:
            plan: The painting plan
            brush: Brush to use (uses default if None)
            progress_callback: Optional callback(stroke_num, total_strokes, status)
            
        Returns:
            StrokeGraph with all planned strokes
        """
        # Create brush if not provided
        if brush is None:
            brush = Brush.create_preset("oil_round")
        
        # Create stroke graph
        graph = StrokeGraph()
        
        # Calculate total strokes
        total_strokes = sum(
            layer.metadata.get("stroke_budget", 0)
            for layer in plan.layers.values()
        )
        
        stroke_count = 0
        
        # Process each layer in order
        for layer_id in plan.layer_order:
            layer = plan.layers.get(layer_id)
            if not layer or not layer.visible:
                continue
                
            # Calculate strokes for this layer
            layer_strokes = layer.metadata.get("stroke_budget", 
                                              total_strokes // len(plan.layers))
            
            # Get brush for this layer
            layer_brush = self._get_brush_for_layer(brush, layer)
            
            # Process regions in this layer
            regions = plan.get_regions_in_layer(layer_id)
            
            for region in regions:
                # Calculate strokes for this region
                region_importance = region.importance / sum(r.importance for r in regions) if regions else 1
                region_strokes = max(1, int(layer_strokes * region_importance))
                
                if progress_callback:
                    progress_callback(stroke_count, total_strokes, 
                                    f"Layer {layer.name}: {region.label}")
                
                # Generate strokes
                strokes = self.generator.generate_strokes(
                    region=region,
                    canvas_size=(plan.canvas_width, plan.canvas_height),
                    brush=layer_brush,
                    num_strokes=region_strokes,
                )
                
                # Add strokes to graph
                for stroke in strokes:
                    graph.add_stroke(stroke, layer_id=layer_id)
                    stroke_count += 1
                    
                    if progress_callback and stroke_count % 100 == 0:
                        progress_callback(stroke_count, total_strokes, f"Stroke {stroke_count}")
        
        return graph
    
    def _get_brush_for_layer(self, base_brush: Brush, 
                            layer) -> Brush:
        """Get brush configuration for a layer."""
        # Clone base brush and adjust for layer
        brush = base_brush.clone()
        
        # Adjust brush size based on layer settings
        if layer.brush_size == "small":
            brush.base_width *= 0.5
        elif layer.brush_size == "large":
            brush.base_width *= 2.0
        
        brush.name = f"{layer.name} Brush"
        
        return brush
    
    def optimize_stroke_graph(self, graph: StrokeGraph,
                             target_image: NDArray[np.uint8],
                             iterations: int = 10) -> StrokeGraph:
        """
        Optimize stroke graph to better match target image.
        
        This is a placeholder for future optimization using diffvg.
        
        Args:
            graph: Input stroke graph
            target_image: Target image to match
            iterations: Number of optimization iterations
            
        Returns:
            Optimized stroke graph
        """
        # In v0.1, just return the input graph
        # Future versions will use diffvg for optimization
        return graph
