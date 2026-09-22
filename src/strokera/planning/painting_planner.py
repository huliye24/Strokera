"""
Painting Planner - Determines painting strategy and layer structure.

Based on Paint-Anything architecture: decides what to paint first,
layer by layer, from background to foreground.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses_json import dataclass_json
import numpy as np
from numpy.typing import NDArray

from strokera.planning.image_analyzer import AnalysisResult, Segment


class PaintLayerType(Enum):
    """Types of painting layers in the plan."""
    BACKGROUND = "background"
    MIDDLE_GROUND = "middle_ground"
    FOREGROUND = "foreground"
    DETAIL = "detail"
    HIGHLIGHT = "highlight"
    SHADOW = "shadow"
    ATMOSPHERE = "atmosphere"


@dataclass
class PaintRegion:
    """
    A region to be painted with its properties.
    
    Represents a coherent area that will receive strokes.
    """
    id: str = field(default_factory=lambda: f"region_{uuid.uuid4().hex[:8]}")
    
    # Source segment (if derived from analysis)
    segment_id: Optional[str] = None
    
    # Layer type
    layer_type: PaintLayerType = PaintLayerType.MIDDLE_GROUND
    
    # Spatial properties
    bbox: Tuple[float, float, float, float] = (0, 0, 0, 0)  # x, y, w, h
    mask: Optional[NDArray[np.bool_]] = None
    
    # Color target
    target_color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    color_tolerance: float = 0.1
    
    # Stroke properties for this region
    stroke_density: float = 1.0      # Relative density of strokes
    stroke_width_base: float = 10.0   # Base stroke width
    stroke_width_variance: float = 0.3 # Variance in stroke width
    
    # Priority (higher = paint earlier within same layer)
    priority: float = 0.5
    
    # Dependencies (region IDs that must be painted first)
    dependencies: Set[str] = field(default_factory=set)
    
    # Metadata
    label: str = "region"
    importance: float = 0.5


@dataclass
class PaintLayer:
    """
    A single layer in the painting plan.
    
    Contains regions to be painted at this stage.
    """
    id: str = field(default_factory=lambda: f"paint_layer_{uuid.uuid4().hex[:8]}")
    
    # Layer properties
    type: PaintLayerType = PaintLayerType.MIDDLE_GROUND
    name: str = "Layer"
    order: int = 0  # Painting order (0 = first)
    
    # Regions in this layer
    regions: List[str] = field(default_factory=list)  # Region IDs
    
    # Stroke settings for this layer
    stroke_density_scale: float = 1.0
    stroke_width_scale: float = 1.0
    
    # Brush settings
    brush_type: str = "default"
    brush_size: str = "medium"  # small, medium, large
    
    # Visibility
    visible: bool = True
    opacity: float = 1.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "order": self.order,
            "regions": self.regions,
            "stroke_density_scale": self.stroke_density_scale,
            "stroke_width_scale": self.stroke_width_scale,
            "brush_type": self.brush_type,
            "brush_size": self.brush_size,
            "visible": self.visible,
            "opacity": self.opacity,
            "metadata": self.metadata,
        }


@dataclass
class PaintingPlan:
    """
    Complete painting plan for an image.
    
    Defines the layer structure and painting order.
    """
    
    id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    
    # Canvas properties
    canvas_width: int = 1024
    canvas_height: int = 1024
    
    # Layers (ordered by painting sequence)
    layers: Dict[str, PaintLayer] = field(default_factory=dict)
    layer_order: List[str] = field(default_factory=list)  # Ordered layer IDs
    
    # Regions (all regions to be painted)
    regions: Dict[str, PaintRegion] = field(default_factory=dict)
    
    # Global settings
    total_strokes_target: int = 1000
    base_stroke_width: float = 10.0
    
    # Brush presets
    brush_presets: Dict[str, str] = field(default_factory=dict)  # layer_type -> brush_name
    
    # Analysis reference
    analysis_id: Optional[str] = None
    
    # Metadata
    strategy: str = "auto"  # auto, portrait, landscape, still_life, abstract
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_regions_in_layer(self, layer_id: str) -> List[PaintRegion]:
        """Get all regions for a layer."""
        layer = self.layers.get(layer_id)
        if not layer:
            return []
        return [self.regions[rid] for rid in layer.regions if rid in self.regions]
    
    def get_painting_order(self) -> List[Tuple[str, str]]:
        """
        Get the order in which to paint regions.
        
        Returns:
            List of (layer_id, region_id) tuples in painting order
        """
        order = []
        for layer_id in self.layer_order:
            layer = self.layers.get(layer_id)
            if not layer or not layer.visible:
                continue
                
            # Sort regions by priority
            regions = self.get_regions_in_layer(layer_id)
            regions_sorted = sorted(regions, key=lambda r: r.priority, reverse=True)
            
            for region in regions_sorted:
                order.append((layer_id, region.id))
                
        return order
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "layers": {lid: layer.to_dict() for lid, layer in self.layers.items()},
            "layer_order": self.layer_order,
            "regions": {rid: {
                "id": r.id,
                "segment_id": r.segment_id,
                "layer_type": r.layer_type.value,
                "bbox": r.bbox,
                "target_color": list(r.target_color),
                "color_tolerance": r.color_tolerance,
                "stroke_density": r.stroke_density,
                "stroke_width_base": r.stroke_width_base,
                "stroke_width_variance": r.stroke_width_variance,
                "priority": r.priority,
                "dependencies": list(r.dependencies),
                "label": r.label,
                "importance": r.importance,
            } for rid, r in self.regions.items()},
            "total_strokes_target": self.total_strokes_target,
            "base_stroke_width": self.base_stroke_width,
            "brush_presets": self.brush_presets,
            "analysis_id": self.analysis_id,
            "strategy": self.strategy,
            "metadata": self.metadata,
        }


class PaintingPlanner:
    """
    Creates painting plans from image analysis.
    
    The planner transforms analysis results into a structured
    painting plan that determines:
    - What layers to create
    - What regions to paint in each layer
    - What brush settings to use
    - Painting order (back to front)
    
    Based on the Paint-Anything architecture.
    """
    
    def __init__(self):
        """Initialize the painting planner."""
        self._strategies = {
            "auto": self._plan_auto,
            "portrait": self._plan_portrait,
            "landscape": self._plan_landscape,
            "still_life": self._plan_still_life,
            "abstract": self._plan_abstract,
        }
    
    def plan(self, analysis: AnalysisResult,
             strategy: str = "auto",
             target_strokes: int = 1000) -> PaintingPlan:
        """
        Create a painting plan from analysis.
        
        Args:
            analysis: Image analysis result
            strategy: Painting strategy to use
            target_strokes: Target number of strokes
            
        Returns:
            PaintingPlan with layer and region structure
        """
        # Get strategy function
        strategy_func = self._strategies.get(strategy, self._plan_auto)
        
        # Create base plan
        plan = PaintingPlan(
            canvas_width=analysis.width,
            canvas_height=analysis.height,
            total_strokes_target=target_strokes,
            analysis_id=analysis.id,
            strategy=strategy,
        )
        
        # Execute strategy
        strategy_func(plan, analysis)
        
        return plan
    
    def _plan_auto(self, plan: PaintingPlan, analysis: AnalysisResult) -> None:
        """Automatic painting plan based on image content."""
        # Create default layers
        self._create_default_layers(plan)
        
        # Assign segments to regions
        for seg_id, segment in analysis.segments.items():
            region = self._segment_to_region(segment)
            plan.regions[region.id] = region
            
            # Assign to appropriate layer based on depth/position
            layer_type = self._classify_segment_layer(segment, analysis)
            layer_id = self._get_layer_for_type(plan, layer_type)
            
            if layer_id:
                plan.layers[layer_id].regions.append(region.id)
        
        # Distribute strokes among layers
        self._distribute_strokes(plan)
    
    def _plan_portrait(self, plan: PaintingPlan, analysis: AnalysisResult) -> None:
        """Portrait-specific painting plan."""
        # Create portrait-optimized layers
        plan.layers = {
            "background": PaintLayer(
                type=PaintLayerType.BACKGROUND,
                name="Background",
                order=0,
                brush_type="watercolor",
                brush_size="large",
            ),
            "hair": PaintLayer(
                type=PaintLayerType.FOREGROUND,
                name="Hair",
                order=1,
                brush_type="oil",
                brush_size="medium",
            ),
            "skin_base": PaintLayer(
                type=PaintLayerType.MIDDLE_GROUND,
                name="Skin Base",
                order=2,
                brush_type="oil",
                brush_size="medium",
            ),
            "features": PaintLayer(
                type=PaintLayerType.DETAIL,
                name="Features",
                order=3,
                brush_type="oil",
                brush_size="small",
            ),
            "eyes": PaintLayer(
                type=PaintLayerType.HIGHLIGHT,
                name="Eyes",
                order=4,
                brush_type="ink",
                brush_size="small",
            ),
        }
        plan.layer_order = ["background", "hair", "skin_base", "features", "eyes"]
        
        # Assign segments
        for seg_id, segment in analysis.segments.items():
            region = self._segment_to_region(segment)
            plan.regions[region.id] = region
            
            # Portrait-specific classification
            layer_type = self._classify_portrait_layer(segment)
            layer_id = self._get_layer_for_type(plan, layer_type)
            
            if layer_id:
                plan.layers[layer_id].regions.append(region.id)
        
        self._distribute_strokes(plan)
    
    def _plan_landscape(self, plan: PaintingPlan, analysis: AnalysisResult) -> None:
        """Landscape-specific painting plan."""
        plan.layers = {
            "sky": PaintLayer(
                type=PaintLayerType.BACKGROUND,
                name="Sky",
                order=0,
                stroke_density_scale=0.5,  # Sparser strokes for sky
                brush_type="watercolor",
                brush_size="large",
            ),
            "mountains": PaintLayer(
                type=PaintLayerType.MIDDLE_GROUND,
                name="Mountains",
                order=1,
                brush_type="watercolor",
                brush_size="medium",
            ),
            "foliage": PaintLayer(
                type=PaintLayerType.MIDDLE_GROUND,
                name="Foliage",
                order=2,
                brush_type="oil",
                brush_size="medium",
            ),
            "ground": PaintLayer(
                type=PaintLayerType.FOREGROUND,
                name="Ground",
                order=3,
                brush_type="oil",
                brush_size="large",
            ),
            "details": PaintLayer(
                type=PaintLayerType.DETAIL,
                name="Details",
                order=4,
                brush_type="oil",
                brush_size="small",
            ),
        }
        plan.layer_order = ["sky", "mountains", "foliage", "ground", "details"]
        
        for seg_id, segment in analysis.segments.items():
            region = self._segment_to_region(segment)
            plan.regions[region.id] = region
            
            layer_type = self._classify_landscape_layer(segment)
            layer_id = self._get_layer_for_type(plan, layer_type)
            
            if layer_id:
                plan.layers[layer_id].regions.append(region.id)
        
        self._distribute_strokes(plan)
    
    def _plan_still_life(self, plan: PaintingPlan, analysis: AnalysisResult) -> None:
        """Still life painting plan."""
        self._plan_auto(plan, analysis)
    
    def _plan_abstract(self, plan: PaintingPlan, analysis: AnalysisResult) -> None:
        """Abstract painting plan with minimal structure."""
        # Just two layers: base and details
        plan.layers = {
            "base": PaintLayer(
                type=PaintLayerType.BACKGROUND,
                name="Base",
                order=0,
                brush_type="oil",
                brush_size="large",
            ),
            "details": PaintLayer(
                type=PaintLayerType.DETAIL,
                name="Details",
                order=1,
                brush_type="oil",
                brush_size="medium",
            ),
        }
        plan.layer_order = ["base", "details"]
        
        for seg_id, segment in analysis.segments.items():
            region = self._segment_to_region(segment)
            region.stroke_density *= 0.5  # More abstract = fewer strokes
            plan.regions[region.id] = region
            plan.layers["base"].regions.append(region.id)
        
        self._distribute_strokes(plan)
    
    def _create_default_layers(self, plan: PaintingPlan) -> None:
        """Create default layer structure."""
        plan.layers = {
            "background": PaintLayer(
                type=PaintLayerType.BACKGROUND,
                name="Background",
                order=0,
                brush_type="watercolor",
                brush_size="large",
            ),
            "middle_ground": PaintLayer(
                type=PaintLayerType.MIDDLE_GROUND,
                name="Middle Ground",
                order=1,
                brush_type="oil",
                brush_size="medium",
            ),
            "foreground": PaintLayer(
                type=PaintLayerType.FOREGROUND,
                name="Foreground",
                order=2,
                brush_type="oil",
                brush_size="large",
            ),
            "details": PaintLayer(
                type=PaintLayerType.DETAIL,
                name="Details",
                order=3,
                brush_type="oil",
                brush_size="small",
            ),
        }
        plan.layer_order = ["background", "middle_ground", "foreground", "details"]
    
    def _segment_to_region(self, segment: Segment) -> PaintRegion:
        """Convert analysis segment to paint region."""
        x, y, w, h = segment.bbox
        
        return PaintRegion(
            segment_id=segment.id,
            bbox=(x / 1000, y / 1000, w / 1000, h / 1000),  # Normalize
            target_color=segment.mean_color,
            stroke_density=segment.importance,
            stroke_width_base=10.0 * (1.0 - segment.importance * 0.5),
            priority=segment.importance,
            label=segment.label,
            importance=segment.importance,
        )
    
    def _classify_segment_layer(self, segment: Segment, 
                                 analysis: AnalysisResult) -> PaintLayerType:
        """Classify which layer a segment belongs to."""
        # Simple classification based on position and depth
        center_y = segment.center[1]
        relative_y = center_y / analysis.height
        
        if relative_y < 0.3:  # Top third
            return PaintLayerType.BACKGROUND
        elif relative_y > 0.7:  # Bottom third
            return PaintLayerType.FOREGROUND
        else:
            return PaintLayerType.MIDDLE_GROUND
    
    def _classify_portrait_layer(self, segment: Segment) -> PaintLayerType:
        """Classify segments for portrait painting."""
        label = segment.label
        center_y = segment.center[1]
        
        if label in ["highlight", "shadow"]:
            return PaintLayerType.DETAIL
        elif "skin" in label:
            return PaintLayerType.MIDDLE_GROUND
        else:
            return PaintLayerType.FOREGROUND
    
    def _classify_landscape_layer(self, segment: Segment) -> PaintLayerType:
        """Classify segments for landscape painting."""
        label = segment.label
        center_y = segment.center[1]
        
        if "sky" in label:
            return PaintLayerType.BACKGROUND
        elif "foliage" in label or "green" in label:
            return PaintLayerType.MIDDLE_GROUND
        else:
            return PaintLayerType.FOREGROUND
    
    def _get_layer_for_type(self, plan: PaintingPlan, 
                            layer_type: PaintLayerType) -> Optional[str]:
        """Get layer ID for a given layer type."""
        for layer_id, layer in plan.layers.items():
            if layer.type == layer_type:
                return layer_id
        return None
    
    def _distribute_strokes(self, plan: PaintingPlan) -> None:
        """Distribute target strokes among layers based on importance."""
        # Calculate total importance
        total_importance = sum(
            r.importance for r in plan.regions.values()
        )
        
        if total_importance == 0:
            return
            
        # Distribute strokes proportionally
        strokes_per_layer: Dict[str, int] = {}
        
        for layer_id, layer in plan.layers.items():
            layer_importance = sum(
                plan.regions[rid].importance 
                for rid in layer.regions 
                if rid in plan.regions
            )
            
            strokes = int(plan.total_strokes_target * layer_importance / total_importance)
            strokes_per_layer[layer_id] = max(1, strokes)
        
        # Update plan with stroke distribution
        for layer_id, strokes in strokes_per_layer.items():
            plan.layers[layer_id].metadata["stroke_budget"] = strokes
