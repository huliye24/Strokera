"""
Canvas - The drawing surface and layer management.

Canvas represents the virtual drawing surface with support for layers,
surfaces, and real-time state tracking.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any, Iterator
from typing_extensions import Protocol
import numpy as np
from numpy.typing import NDArray


class BlendMode(Enum):
    """Standard blend modes for layers."""
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    DARKEN = "darken"
    LIGHTEN = "lighten"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    DIFFERENCE = "difference"
    EXCLUSION = "exclusion"
    HUE = "hue"
    SATURATION = "saturation"
    COLOR = "color"
    LUMINOSITY = "luminosity"


class LayerType(Enum):
    """Types of canvas layers."""
    PAINT = "paint"           # Regular paint layer
    TEXTURE = "texture"        # Surface texture
    REFERENCE = "reference"    # Reference image (not painted on)
    ADJUSTMENT = "adjustment" # Adjustment layer
    GROUP = "group"            # Layer group


@dataclass
class Layer:
    """
    A single layer in the canvas.
    
    Layers can contain paint, reference images, textures, or adjustments.
    """
    
    id: str = field(default_factory=lambda: f"layer_{uuid.uuid4().hex[:8]}")
    name: str = "Layer"
    type: LayerType = LayerType.PAINT
    
    # Visibility and editing
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    
    # Content
    pixels: Optional[NDArray[np.uint8]] = None  # RGBA pixels
    
    # For reference layers
    reference_path: Optional[str] = None
    
    # Layer stack
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize pixel buffer if needed."""
        pass  # Size set by Canvas
    
    @property
    def is_empty(self) -> bool:
        """Check if layer has any content."""
        if self.pixels is None:
            return True
        return self.pixels.sum() == 0
    
    def clear(self) -> None:
        """Clear the layer content."""
        if self.pixels is not None:
            self.pixels.fill(0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "visible": self.visible,
            "locked": self.locked,
            "opacity": self.opacity,
            "blend_mode": self.blend_mode.value,
            "reference_path": self.reference_path,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], pixels: Optional[NDArray[np.uint8]] = None) -> Layer:
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id", f"layer_{uuid.uuid4().hex[:8]}"),
            name=data.get("name", "Layer"),
            type=LayerType(data.get("type", "paint")),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
            opacity=data.get("opacity", 1.0),
            blend_mode=BlendMode(data.get("blend_mode", "normal")),
            reference_path=data.get("reference_path"),
            parent_id=data.get("parent_id"),
            child_ids=data.get("child_ids", []),
            metadata=data.get("metadata", {}),
            pixels=pixels,
        )


@dataclass
class CanvasState:
    """
    Snapshot of canvas state for undo/redo.
    
    Stores the complete state needed to restore the canvas.
    """
    timestamp: float = 0.0
    layers: Dict[str, Layer] = field(default_factory=dict)
    active_layer_id: Optional[str] = None
    zoom: float = 1.0
    pan: Tuple[float, float] = (0.0, 0.0)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Surface:
    """
    Represents the painting surface/material.
    
    Surface affects how paint interacts with the canvas:
    - Paper texture
    - Canvas grain
    - Absorbency
    - Wet behavior
    """
    
    id: str = field(default_factory=lambda: f"surface_{uuid.uuid4().hex[:8]}")
    name: str = "Canvas"
    
    # Texture
    texture_map: Optional[NDArray[np.float32]] = None
    texture_strength: float = 0.3
    
    # Material properties
    absorbency: float = 0.5  # How much paint is absorbed
    roughness: float = 0.3   # Surface roughness
    grain_size: float = 1.0  # Size of surface grain
    
    # Wet behavior
    wet_spread: float = 0.1  # How much paint spreads when wet
    dry_edge: float = 0.2    # Softening of edges when drying
    
    # Base color
    base_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    
    @classmethod
    def create_preset(cls, preset_name: str) -> Surface:
        """Create a surface from a preset."""
        presets = {
            "canvas": cls._canvas_preset(),
            "watercolor_paper": cls._watercolor_paper_preset(),
            "smooth_paper": cls._smooth_paper_preset(),
            "canvas_rough": cls._rough_canvas_preset(),
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")
            
        return presets[preset_name]()
    
    @staticmethod
    def _canvas_preset() -> Surface:
        return cls(
            name="Canvas",
            texture_strength=0.3,
            absorbency=0.4,
            roughness=0.3,
            grain_size=1.0,
            wet_spread=0.1,
        )
    
    @staticmethod
    def _watercolor_paper_preset() -> Surface:
        return cls(
            name="Watercolor Paper",
            texture_strength=0.6,
            absorbency=0.7,
            roughness=0.5,
            grain_size=1.5,
            wet_spread=0.3,
            dry_edge=0.4,
        )
    
    @staticmethod
    def _smooth_paper_preset() -> Surface:
        return cls(
            name="Smooth Paper",
            texture_strength=0.1,
            absorbency=0.3,
            roughness=0.1,
            grain_size=0.5,
        )
    
    @staticmethod
    def _rough_canvas_preset() -> Surface:
        return cls(
            name="Rough Canvas",
            texture_strength=0.5,
            absorbency=0.5,
            roughness=0.6,
            grain_size=2.0,
            wet_spread=0.15,
        )


class Canvas:
    """
    The virtual drawing surface.
    
    Canvas manages layers, surface properties, and provides
    rendering and state management.
    """
    
    def __init__(self, width: int, height: int, background: Tuple[int, int, int] = (255, 255, 255)):
        """
        Create a new canvas.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
            background: Background color (RGB)
        """
        self.width = width
        self.height = height
        self.background = background
        
        # Layers
        self.layers: Dict[str, Layer] = {}
        self.active_layer_id: Optional[str] = None
        self._create_default_layer()
        
        # Surface
        self.surface = Surface.create_preset("canvas")
        
        # State history for undo/redo
        self._history: List[CanvasState] = []
        self._history_index: int = -1
        self._max_history: int = 50
        
        # Metadata
        self.metadata: Dict[str, Any] = {}
    
    def _create_default_layer(self) -> None:
        """Create the default layer."""
        layer = Layer(
            name="Background",
            type=LayerType.PAINT,
            pixels=np.zeros((self.height, self.width, 4), dtype=np.uint8),
        )
        
        # Fill with background color
        layer.pixels[:, :, 0] = self.background[0]
        layer.pixels[:, :, 1] = self.background[1]
        layer.pixels[:, :, 2] = self.background[2]
        layer.pixels[:, :, 3] = 255
        
        self.layers[layer.id] = layer
        self.active_layer_id = layer.id
    
    # ============ Layer Management ============
    
    def add_layer(self, name: Optional[str] = None, 
                  layer_type: LayerType = LayerType.PAINT) -> Layer:
        """
        Add a new layer.
        
        Args:
            name: Optional layer name
            layer_type: Type of layer
            
        Returns:
            The new layer
        """
        layer = Layer(
            name=name or f"Layer {len(self.layers) + 1}",
            type=layer_type,
            pixels=np.zeros((self.height, self.width, 4), dtype=np.uint8),
        )
        
        self.layers[layer.id] = layer
        self.active_layer_id = layer.id
        
        return layer
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer."""
        if layer_id not in self.layers:
            return False
            
        if len(self.layers) <= 1:
            return False  # Can't remove last layer
            
        del self.layers[layer_id]
        
        if self.active_layer_id == layer_id:
            self.active_layer_id = next(iter(self.layers.keys()))
            
        return True
    
    def get_active_layer(self) -> Optional[Layer]:
        """Get the currently active layer."""
        if self.active_layer_id:
            return self.layers.get(self.active_layer_id)
        return None
    
    def move_layer(self, layer_id: str, new_index: int) -> bool:
        """Move a layer to a new position in the stack."""
        # For now, just reorder by ID (simplified)
        return True
    
    # ============ Rendering ============
    
    def render(self) -> NDArray[np.uint8]:
        """
        Render the complete canvas to an RGB image.
        
        Returns:
            Rendered image as numpy array (H, W, 3)
        """
        result = np.zeros((self.height, self.width, 3), dtype=np.float32)
        
        # Start with background
        result[:, :, 0] = self.background[0] / 255.0
        result[:, :, 1] = self.background[1] / 255.0
        result[:, :, 2] = self.background[2] / 255.0
        
        # Composite layers from bottom to top
        for layer in self.layers.values():
            if not layer.visible:
                continue
                
            if layer.pixels is None:
                continue
                
            alpha = layer.pixels[:, :, 3:4].astype(np.float32) / 255.0 * layer.opacity
            color = layer.pixels[:, :, :3].astype(np.float32) / 255.0
            
            # Simple alpha compositing
            result = result * (1 - alpha) + color * alpha
            
        return (result * 255).astype(np.uint8)
    
    def render_with_alpha(self) -> NDArray[np.uint8]:
        """Render with alpha channel for layer editing."""
        result = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        
        for layer in self.layers.values():
            if not layer.visible:
                continue
                
            if layer.pixels is None:
                continue
                
            # Simplified compositing
            src = layer.pixels.astype(np.float32)
            dst = result.astype(np.float32)
            
            src_alpha = src[:, :, 3:4] / 255.0 * layer.opacity
            dst_alpha = dst[:, :, 3:4] / 255.0
            
            out_alpha = src_alpha + dst_alpha * (1 - src_alpha)
            out_rgb = np.where(
                out_alpha > 0,
                (src[:, :, :3] * src_alpha + dst[:, :, :3] * dst_alpha * (1 - src_alpha)) / out_alpha,
                0
            )
            
            result[:, :, :3] = np.clip(out_rgb, 0, 255).astype(np.uint8)
            result[:, :, 3] = np.clip(out_alpha * 255, 0, 255).astype(np.uint8)
            
        return result
    
    # ============ State Management ============
    
    def save_state(self) -> None:
        """Save current state for undo."""
        # Truncate future history if we're not at the end
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]
            
        # Create state snapshot
        state = CanvasState(
            layers={lid: layer.to_dict() for lid, layer in self.layers.items()},
            active_layer_id=self.active_layer_id,
        )
        
        self._history.append(state)
        
        # Limit history size
        if len(self._history) > self._max_history:
            self._history.pop(0)
            
        self._history_index = len(self._history) - 1
    
    def undo(self) -> bool:
        """Undo the last operation."""
        if self._history_index <= 0:
            return False
            
        self._history_index -= 1
        self._restore_state(self._history[self._history_index])
        return True
    
    def redo(self) -> bool:
        """Redo the last undone operation."""
        if self._history_index >= len(self._history) - 1:
            return False
            
        self._history_index += 1
        self._restore_state(self._history[self._history_index])
        return True
    
    def _restore_state(self, state: CanvasState) -> None:
        """Restore a saved state."""
        self.layers = {}
        for lid, layer_data in state.layers.items():
            self.layers[lid] = Layer.from_dict(layer_data)
        self.active_layer_id = state.active_layer_id
    
    # ============ I/O ============
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "background": list(self.background),
            "layers": {lid: layer.to_dict() for lid, layer in self.layers.items()},
            "active_layer_id": self.active_layer_id,
            "surface": {
                "name": self.surface.name,
                "texture_strength": self.surface.texture_strength,
                "absorbency": self.surface.absorbency,
            },
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Canvas:
        """Deserialize from dictionary."""
        canvas = cls(
            width=data["width"],
            height=data["height"],
            background=tuple(data.get("background", [255, 255, 255])),
        )
        
        canvas.layers = {}
        for lid, layer_data in data.get("layers", {}).items():
            canvas.layers[lid] = Layer.from_dict(layer_data)
            
        canvas.active_layer_id = data.get("active_layer_id")
        
        if data.get("surface"):
            surface_data = data["surface"]
            canvas.surface = Surface(
                name=surface_data.get("name", "Canvas"),
                texture_strength=surface_data.get("texture_strength", 0.3),
                absorbency=surface_data.get("absorbency", 0.5),
            )
        
        canvas.metadata = data.get("metadata", {})
        
        return canvas
