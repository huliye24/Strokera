"""
Brush - Data structures for brush types and their physics.

Defines various brush types and the BrushEngine for rendering strokes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any, Callable
from typing_extensions import Protocol
import numpy as np
from numpy.typing import NDArray


class BrushType(Enum):
    """Categories of brush types."""
    OIL = "oil"
    WATERCOLOR = "watercolor"
    ACRYLIC = "acrylic"
    INK = "ink"
    PENCIL = "pencil"
    CHARCOAL = "charcoal"
    MARKER = "marker"
    PASTEL = "pastel"
    SPRAY = "spray"
    TEXTURED = "textured"


@dataclass
class BrushPhysics:
    """
    Physical properties that affect how a brush behaves.
    
    These parameters control the brush's interaction with the canvas,
    including pressure response, tilt, rotation, and texture.
    """
    # Pressure response
    pressure_min: float = 0.1   # Minimum opacity at light pressure
    pressure_max: float = 1.0   # Maximum opacity at full pressure
    pressure_curve: float = 1.0 # Curve exponent (1 = linear, 2 = squared, etc.)
    
    # Width response
    width_pressure_scale: float = 1.0  # How much pressure affects width
    width_tilt_scale: float = 0.0     # How much tilt affects width
    
    # Tilt and rotation
    tilt_sensitivity: float = 0.0  # How much tilt affects the brush
    auto_rotation: bool = True     # Automatically rotate to stroke direction
    
    # Texture
    texture_intensity: float = 0.0  # How much texture noise
    texture_scale: float = 1.0       # Scale of texture pattern
    
    # Bleeding
    bleed_amount: float = 0.0    # How much paint spreads
    bleed_variance: float = 0.0  # Random variation in bleeding
    
    # Layering
    blend_mode: str = "normal"    # How new strokes blend with existing
    layer_ buildup: float = 0.1   # How quickly opacity builds up
    
    # Drying
    drying_time: float = 0.0     # Time before stroke becomes permanent
    wet_edge: bool = False        # Keep soft edges when wet
    
    
@dataclass 
class Brush:
    """
    Defines a brush type with all its parameters.
    
    A brush determines how strokes are rendered:
    - Shape profile (how width varies across the stroke)
    - Texture (surface noise/pattern)
    - Physics (pressure response, etc.)
    - Pigment behavior (how color is deposited)
    """
    
    id: str = field(default_factory=lambda: f"brush_{uuid.uuid4().hex[:8]}")
    name: str = "Default Brush"
    type: BrushType = BrushType.OIL
    
    # Shape profile
    shape_profile: str = "round"  # round, flat, fan, custom
    base_width: float = 10.0
    taper_enabled: bool = True
    taper_start: float = 0.0   # Taper at start (0-1)
    taper_end: float = 0.2     # Taper at end (0-1)
    
    # Custom shape (optional)
    custom_profile: Optional[NDArray[np.float32]] = None
    
    # Texture
    texture: Optional[NDArray[np.float32]] = None  # 2D texture pattern
    texture_mask: Optional[NDArray[np.float32]] = None  # Alpha mask for brush shape
    
    # Physics
    physics: BrushPhysics = field(default_factory=BrushPhysics)
    
    # Color behavior
    opacity_per_pass: float = 1.0  # How much opacity accumulates per stroke
    scattering: float = 0.0        # Random scattering of pigment
    bristle_gaps: float = 0.0     # For dry brush effects
    
    # Oil paint specific
    impasto: float = 0.0          # 3D texture height
    glaze: float = 0.0            # Transparency for layering
    
    # Watercolor specific
    granulation: float = 0.0       # Granular texture effect
    wet_spread: float = 0.0       # How much paint spreads when wet
    
    # Marker specific
    bleed: float = 0.0            # How much marker bleeds
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create_preset(cls, preset_name: str) -> Brush:
        """Create a brush from a preset."""
        presets = {
            "oil_round": cls._oil_round_preset(),
            "oil_flat": cls._oil_flat_preset(),
            "watercolor": cls._watercolor_preset(),
            "marker": cls._marker_preset(),
            "ink_brush": cls._ink_brush_preset(),
            "pencil": cls._pencil_preset(),
            "charcoal": cls._charcoal_preset(),
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
            
        return presets[preset_name]()
    
    @staticmethod
    def _oil_round_preset() -> Brush:
        brush = Brush(
            name="Oil Round",
            type=BrushType.OIL,
            shape_profile="round",
            base_width=20.0,
            taper_enabled=True,
            physics=BrushPhysics(
                pressure_min=0.3,
                pressure_max=1.0,
                pressure_curve=1.5,
                width_pressure_scale=0.5,
                blend_mode="normal",
            ),
            impasto=0.3,
            glaze=0.2,
        )
        return brush
    
    @staticmethod
    def _oil_flat_preset() -> Brush:
        brush = Brush(
            name="Oil Flat",
            type=BrushType.OIL,
            shape_profile="flat",
            base_width=30.0,
            taper_enabled=True,
            physics=BrushPhysics(
                pressure_min=0.4,
                pressure_max=1.0,
                auto_rotation=True,
            ),
            impasto=0.4,
        )
        return brush
    
    @staticmethod
    def _watercolor_preset() -> Brush:
        brush = Brush(
            name="Watercolor",
            type=BrushType.WATERCOLOR,
            shape_profile="round",
            base_width=15.0,
            taper_enabled=True,
            physics=BrushPhysics(
                pressure_min=0.1,
                pressure_max=0.7,
                pressure_curve=2.0,
                bleed_amount=0.3,
                bleed_variance=0.1,
            ),
            opacity_per_pass=0.5,
            granulation=0.2,
            wet_spread=0.4,
        )
        return brush
    
    @staticmethod
    def _marker_preset() -> Brush:
        brush = Brush(
            name="Marker",
            type=BrushType.MARKER,
            shape_profile="round",
            base_width=8.0,
            taper_enabled=False,
            physics=BrushPhysics(
                pressure_min=0.8,
                pressure_max=1.0,
                blend_mode="multiply",
            ),
            bleed=0.15,
        )
        return brush
    
    @staticmethod
    def _ink_brush_preset() -> Brush:
        brush = Brush(
            name="Ink Brush",
            type=BrushType.INK,
            shape_profile="round",
            base_width=12.0,
            taper_enabled=True,
            taper_start=0.1,
            taper_end=0.3,
            physics=BrushPhysics(
                pressure_min=0.2,
                pressure_max=1.0,
                pressure_curve=1.8,
                width_pressure_scale=0.8,
            ),
            scattering=0.05,
        )
        return brush
    
    @staticmethod
    def _pencil_preset() -> Brush:
        brush = Brush(
            name="Pencil",
            type=BrushType.PENCIL,
            shape_profile="round",
            base_width=3.0,
            taper_enabled=False,
            physics=BrushPhysics(
                pressure_min=0.3,
                pressure_max=1.0,
                pressure_curve=1.2,
            ),
            scattering=0.1,
            bristle_gaps=0.2,
        )
        return brush
    
    @staticmethod
    def _charcoal_preset() -> Brush:
        brush = Brush(
            name="Charcoal",
            type=BrushType.CHARCOAL,
            shape_profile="round",
            base_width=15.0,
            taper_enabled=True,
            physics=BrushPhysics(
                pressure_min=0.1,
                pressure_max=0.9,
                blend_mode="multiply",
            ),
            scattering=0.3,
            bristle_gaps=0.3,
        )
        return brush
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        physics_dict = {
            "pressure_min": self.physics.pressure_min,
            "pressure_max": self.physics.pressure_max,
            "pressure_curve": self.physics.pressure_curve,
            "width_pressure_scale": self.physics.width_pressure_scale,
            "width_tilt_scale": self.physics.width_tilt_scale,
            "tilt_sensitivity": self.physics.tilt_sensitivity,
            "auto_rotation": self.physics.auto_rotation,
            "texture_intensity": self.physics.texture_intensity,
            "texture_scale": self.physics.texture_scale,
            "bleed_amount": self.physics.bleed_amount,
            "bleed_variance": self.physics.bleed_variance,
            "blend_mode": self.physics.blend_mode,
            "layer_buildup": self.physics.layer_buildup,
            "drying_time": self.physics.drying_time,
            "wet_edge": self.physics.wet_edge,
        }
        
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "shape_profile": self.shape_profile,
            "base_width": self.base_width,
            "taper_enabled": self.taper_enabled,
            "taper_start": self.taper_start,
            "taper_end": self.taper_end,
            "physics": physics_dict,
            "opacity_per_pass": self.opacity_per_pass,
            "scattering": self.scattering,
            "bristle_gaps": self.bristle_gaps,
            "impasto": self.impasto,
            "glaze": self.glaze,
            "granulation": self.granulation,
            "wet_spread": self.wet_spread,
            "bleed": self.bleed,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Brush:
        """Deserialize from dictionary."""
        physics_data = data.get("physics", {})
        physics = BrushPhysics(
            pressure_min=physics_data.get("pressure_min", 0.1),
            pressure_max=physics_data.get("pressure_max", 1.0),
            pressure_curve=physics_data.get("pressure_curve", 1.0),
            width_pressure_scale=physics_data.get("width_pressure_scale", 1.0),
            width_tilt_scale=physics_data.get("width_tilt_scale", 0.0),
            tilt_sensitivity=physics_data.get("tilt_sensitivity", 0.0),
            auto_rotation=physics_data.get("auto_rotation", True),
            texture_intensity=physics_data.get("texture_intensity", 0.0),
            texture_scale=physics_data.get("texture_scale", 1.0),
            bleed_amount=physics_data.get("bleed_amount", 0.0),
            bleed_variance=physics_data.get("bleed_variance", 0.0),
            blend_mode=physics_data.get("blend_mode", "normal"),
            layer_buildup=physics_data.get("layer_buildup", 0.1),
            drying_time=physics_data.get("drying_time", 0.0),
            wet_edge=physics_data.get("wet_edge", False),
        )
        
        return cls(
            id=data.get("id", f"brush_{uuid.uuid4().hex[:8]}"),
            name=data.get("name", "Brush"),
            type=BrushType(data.get("type", "oil")),
            shape_profile=data.get("shape_profile", "round"),
            base_width=data.get("base_width", 10.0),
            taper_enabled=data.get("taper_enabled", True),
            taper_start=data.get("taper_start", 0.0),
            taper_end=data.get("taper_end", 0.2),
            physics=physics,
            opacity_per_pass=data.get("opacity_per_pass", 1.0),
            scattering=data.get("scattering", 0.0),
            bristle_gaps=data.get("bristle_gaps", 0.0),
            impasto=data.get("impasto", 0.0),
            glaze=data.get("glaze", 0.0),
            granulation=data.get("granulation", 0.0),
            wet_spread=data.get("wet_spread", 0.0),
            bleed=data.get("bleed", 0.0),
            metadata=data.get("metadata", {}),
        )


class BrushEngine:
    """
    Renders strokes using brush physics and parameters.
    
    The BrushEngine takes Stroke objects and renders them to a canvas
    image, applying brush-specific physics and textures.
    """
    
    def __init__(self, canvas_size: Tuple[int, int]):
        """
        Initialize the brush engine.
        
        Args:
            canvas_size: (width, height) of the target canvas
        """
        self.canvas_size = canvas_size
        self._cache: Dict[str, Any] = {}
        
    def render_stroke(self, stroke, brush: Brush, 
                      target: NDArray[np.uint8],
                      mask: Optional[NDArray[np.float32]] = None) -> None:
        """
        Render a single stroke to the target image.
        
        Args:
            stroke: Stroke object to render
            brush: Brush object defining appearance
            target: Target RGB image (will be modified in place)
            mask: Optional pre-computed stroke mask
        """
        if not stroke.path or len(stroke.path) < 2:
            return
            
        # Create stroke mask
        if mask is None:
            mask = self._create_stroke_mask(stroke, brush)
            
        # Get color
        color = np.array(stroke.color, dtype=np.float32) * 255
        opacity = stroke.opacity * brush.opacity_per_pass
        
        # Apply mask with alpha blending
        h, w = mask.shape[:2]
        
        # Ensure mask is 2D
        if len(mask.shape) == 3:
            mask = mask[:, :, 0]
            
        # Ensure target is float for blending
        target_float = target.astype(np.float32)
        
        # Apply color and mask
        for c in range(3):
            target_float[:, :, c] = target_float[:, :, c] * (1 - mask * opacity) + color[c] * mask * opacity
            
        target[:] = np.clip(target_float, 0, 255).astype(np.uint8)
        
    def _create_stroke_mask(self, stroke, brush: Brush) -> NDArray[np.float32]:
        """
        Create a grayscale mask for the stroke.
        
        This is the core rendering function that generates the brush shape
        along the stroke path.
        """
        h, w = self.canvas_size
        
        # Create empty mask
        mask = np.zeros((h, w), dtype=np.float32)
        
        # Get stroke widths at each point
        widths = stroke.get_effective_widths()
        
        # Sample stroke path
        num_samples = max(len(stroke.path), 50)
        samples = stroke.sample_points(num_samples)
        
        if not samples:
            return mask
            
        # Draw stroke segments
        for i in range(len(samples) - 1):
            x1, y1, t1 = samples[i]
            x2, y2, t2 = samples[i + 1]
            
            # Interpolate width
            t = (t1 + t2) / 2
            idx = min(int(t * len(widths)), len(widths) - 1)
            width = widths[idx] if idx < len(widths) else widths[-1]
            
            # Draw line segment
            self._draw_line(mask, x1, y1, x2, y2, width / 2)
            
        return mask
    
    def _draw_line(self, mask: NDArray[np.float32], 
                   x1: float, y1: float, 
                   x2: float, y2: float,
                   radius: float) -> None:
        """
        Draw a soft-edged line on the mask.
        
        Uses Bresenham-like algorithm with distance-based falloff.
        """
        h, w = mask.shape
        
        # Convert to int for indexing
        ix1, iy1 = int(x1), int(y1)
        ix2, iy2 = int(x2), int(y2)
        
        # Get bounding box
        min_x = max(0, int(min(ix1, ix2) - radius - 1))
        max_x = min(w, int(max(ix1, ix2) + radius + 1))
        min_y = max(0, int(min(iy1, iy2) - radius - 1))
        max_y = min(h, int(max(iy1, iy2) + radius + 1))
        
        # Sample points in bounding box
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                # Calculate distance to line segment
                dist = self._point_to_line_distance(x, y, x1, y1, x2, y2)
                
                if dist < radius:
                    # Soft falloff
                    alpha = 1.0 - (dist / radius) ** 2
                    mask[y, x] = max(mask[y, x], alpha)
    
    @staticmethod
    def _point_to_line_distance(px: float, py: float,
                                 x1: float, y1: float,
                                 x2: float, y2: float) -> float:
        """Calculate perpendicular distance from point to line segment."""
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx*dx + dy*dy
        
        if length_sq < 1e-10:
            return np.sqrt((px - x1)**2 + (py - y1)**2)
            
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        return np.sqrt((px - proj_x)**2 + (py - proj_y)**2)
    
    def render_stroke_graph(self, stroke_graph, brush: Brush,
                           target: NDArray[np.uint8]) -> None:
        """
        Render all strokes in a StrokeGraph.
        
        Args:
            stroke_graph: StrokeGraph containing strokes
            brush: Brush to use for rendering
            target: Target RGB image
        """
        # Render in order
        for stroke in stroke_graph.get_strokes_in_order():
            self.render_stroke(stroke, brush, target)
