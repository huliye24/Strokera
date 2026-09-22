"""
StrokeGraph - Graph structure representing the painting process.

StrokeGraph maintains the full sequence and relationships of strokes,
supporting progressive rendering, editing, and optimization.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Iterator, Tuple, Any
from collections import defaultdict
import numpy as np

from strokera.core.stroke import Stroke, StrokeType


@dataclass
class StrokeGraph:
    """
    A graph structure representing the complete painting process.
    
    StrokeGraph maintains:
    - Ordered sequence of strokes (for rendering)
    - Layer assignments
    - Grouping relationships
    - Dependencies (e.g., stroke A must precede stroke B)
    - Spatial index for fast queries
    
    The graph can be traversed in:
    - Render order (sequential painting)
    - Layer order (back to front)
    - Dependency order (respecting constraints)
    """
    
    id: str = field(default_factory=lambda: f"graph_{uuid.uuid4().hex[:8]}")
    strokes: Dict[str, Stroke] = field(default_factory=dict)
    stroke_order: List[str] = field(default_factory=list)  # Ordered stroke IDs
    
    # Layer management
    layers: Dict[str, List[str]] = field(default_factory=dict)  # layer_id -> stroke_ids
    
    # Grouping (for objects, regions, etc.)
    groups: Dict[str, Set[str]] = field(default_factory=dict)  # group_id -> stroke_ids
    
    # Dependencies (directed edges)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)  # stroke_id -> must_render_before
    
    # Spatial index (approximate)
    _spatial_index: Dict[str, Tuple[float, float, float, float]] = field(default_factory=dict)
    
    # Statistics
    _stats: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default layer."""
        if "default" not in self.layers:
            self.layers["default"] = []
    
    # ============ Stroke Management ============
    
    def add_stroke(self, stroke: Stroke, layer_id: str = "default", 
                   group_id: Optional[str] = None) -> str:
        """
        Add a stroke to the graph.
        
        Args:
            stroke: The stroke to add
            layer_id: Layer assignment
            group_id: Optional group assignment
            
        Returns:
            The stroke ID
        """
        stroke_id = stroke.id
        
        # Add to strokes dict
        self.strokes[stroke_id] = stroke
        stroke.layer_id = layer_id
        
        # Add to order
        self.stroke_order.append(stroke_id)
        stroke.render_order = len(self.stroke_order) - 1
        
        # Add to layer
        if layer_id not in self.layers:
            self.layers[layer_id] = []
        self.layers[layer_id].append(stroke_id)
        
        # Add to group if specified
        if group_id:
            self.add_to_group(stroke_id, group_id)
        
        # Update spatial index
        self._update_spatial_index(stroke_id)
        
        # Invalidate stats
        self._stats = {}
        
        return stroke_id
    
    def remove_stroke(self, stroke_id: str) -> Optional[Stroke]:
        """Remove a stroke from the graph."""
        if stroke_id not in self.strokes:
            return None
            
        stroke = self.strokes[stroke_id]
        
        # Remove from stroke_order
        self.stroke_order.remove(stroke_id)
        
        # Remove from layer
        layer_id = stroke.layer_id
        if layer_id in self.layers:
            self.layers[layer_id].remove(stroke_id)
        
        # Remove from groups
        for group_id, members in self.groups.items():
            members.discard(stroke_id)
        
        # Remove dependencies
        self.dependencies.pop(stroke_id, None)
        for deps in self.dependencies.values():
            deps.discard(stroke_id)
        
        # Remove from spatial index
        self._spatial_index.pop(stroke_id, None)
        
        # Remove from strokes dict
        del self.strokes[stroke_id]
        
        # Invalidate stats
        self._stats = {}
        
        # Update render orders
        for i, sid in enumerate(self.stroke_order):
            self.strokes[sid].render_order = i
        
        return stroke
    
    def get_stroke(self, stroke_id: str) -> Optional[Stroke]:
        """Get a stroke by ID."""
        return self.strokes.get(stroke_id)
    
    def get_strokes_in_order(self) -> Iterator[Stroke]:
        """Iterate over strokes in render order."""
        for stroke_id in self.stroke_order:
            yield self.strokes[stroke_id]
    
    def get_strokes_by_layer(self, layer_id: str) -> Iterator[Stroke]:
        """Iterate over strokes in a specific layer."""
        for stroke_id in self.layers.get(layer_id, []):
            if stroke_id in self.strokes:
                yield self.strokes[stroke_id]
    
    def get_strokes_by_group(self, group_id: str) -> Iterator[Stroke]:
        """Iterate over strokes in a specific group."""
        for stroke_id in self.groups.get(group_id, []):
            if stroke_id in self.strokes:
                yield self.strokes[stroke_id]
    
    # ============ Layer Management ============
    
    def add_layer(self, layer_id: str) -> None:
        """Create a new layer."""
        if layer_id not in self.layers:
            self.layers[layer_id] = []
    
    def remove_layer(self, layer_id: str) -> List[Stroke]:
        """Remove a layer and return its strokes."""
        if layer_id == "default":
            raise ValueError("Cannot remove default layer")
            
        stroke_ids = self.layers.pop(layer_id, [])
        strokes = []
        for stroke_id in stroke_ids:
            if stroke_id in self.strokes:
                strokes.append(self.strokes[stroke_id])
        return strokes
    
    def move_stroke_to_layer(self, stroke_id: str, new_layer_id: str) -> None:
        """Move a stroke to a different layer."""
        stroke = self.strokes.get(stroke_id)
        if not stroke:
            return
            
        old_layer = stroke.layer_id
        
        # Remove from old layer
        if old_layer in self.layers:
            if stroke_id in self.layers[old_layer]:
                self.layers[old_layer].remove(stroke_id)
        
        # Add to new layer
        if new_layer_id not in self.layers:
            self.layers[new_layer_id] = []
        self.layers[new_layer_id].append(stroke_id)
        
        stroke.layer_id = new_layer_id
    
    # ============ Group Management ============
    
    def add_to_group(self, stroke_id: str, group_id: str) -> None:
        """Add a stroke to a group."""
        if group_id not in self.groups:
            self.groups[group_id] = set()
        self.groups[group_id].add(stroke_id)
    
    def remove_from_group(self, stroke_id: str, group_id: str) -> None:
        """Remove a stroke from a group."""
        if group_id in self.groups:
            self.groups[group_id].discard(stroke_id)
    
    def create_group_from_region(self, region: Tuple[float, float, float, float],
                                 group_id: Optional[str] = None) -> str:
        """
        Create a group containing all strokes within a bounding region.
        
        Args:
            region: (min_x, min_y, max_x, max_y)
            group_id: Optional custom group ID
            
        Returns:
            The group ID
        """
        if group_id is None:
            group_id = f"region_{uuid.uuid4().hex[:8]}"
            
        self.groups[group_id] = set()
        
        min_x, min_y, max_x, max_y = region
        for stroke_id, bbox in self._spatial_index.items():
            sx_min, sy_min, sx_max, sy_max = bbox
            # Check intersection
            if not (sx_max < min_x or sx_min > max_x or sy_max < min_y or sy_min > max_y):
                self.groups[group_id].add(stroke_id)
                
        return group_id
    
    # ============ Dependency Management ============
    
    def add_dependency(self, before_id: str, after_id: str) -> None:
        """
        Add a dependency: stroke `before_id` must be rendered before `after_id`.
        """
        if after_id not in self.dependencies:
            self.dependencies[after_id] = set()
        self.dependencies[after_id].add(before_id)
    
    def remove_dependency(self, before_id: str, after_id: str) -> None:
        """Remove a dependency."""
        if after_id in self.dependencies:
            self.dependencies[after_id].discard(before_id)
    
    def get_render_order_with_deps(self) -> List[str]:
        """
        Get render order respecting dependencies.
        
        Returns:
            List of stroke IDs in topological order
        """
        # Build in-degree map
        in_degree = defaultdict(int)
        for stroke_id in self.stroke_order:
            in_degree[stroke_id] = 0
            
        for after_id, befores in self.dependencies.items():
            for before_id in befores:
                if before_id in self.stroke_order:
                    in_degree[after_id] += 1
        
        # Kahn's algorithm
        queue = [sid for sid in self.stroke_order if in_degree[sid] == 0]
        result = []
        
        while queue:
            stroke_id = queue.pop(0)
            result.append(stroke_id)
            
            for after_id, befores in self.dependencies.items():
                if stroke_id in befores:
                    in_degree[after_id] -= 1
                    if in_degree[after_id] == 0:
                        queue.append(after_id)
        
        # If there's a cycle, fall back to original order
        if len(result) < len(self.stroke_order):
            # Filter to only strokes that exist
            result = [sid for sid in result if sid in self.strokes]
            
        return result
    
    # ============ Spatial Queries ============
    
    def _update_spatial_index(self, stroke_id: str) -> None:
        """Update spatial index for a stroke."""
        stroke = self.strokes.get(stroke_id)
        if stroke:
            self._spatial_index[stroke_id] = stroke.get_bounding_box()
    
    def query_region(self, region: Tuple[float, float, float, float]) -> List[Stroke]:
        """
        Query all strokes that intersect with a region.
        
        Args:
            region: (min_x, min_y, max_x, max_y)
            
        Returns:
            List of strokes intersecting the region
        """
        min_x, min_y, max_x, max_y = region
        result = []
        
        for stroke_id, bbox in self._spatial_index.items():
            sx_min, sy_min, sx_max, sy_max = bbox
            # Check intersection
            if not (sx_max < min_x or sx_min > max_x or sy_max < min_y or sy_min > max_y):
                result.append(self.strokes[stroke_id])
                
        return result
    
    def query_point(self, x: float, y: float, tolerance: float = 5.0) -> List[Stroke]:
        """
        Query all strokes near a point.
        
        Args:
            x, y: Point coordinates
            tolerance: Search radius
            
        Returns:
            List of strokes near the point
        """
        return self.query_region((x - tolerance, y - tolerance, 
                                  x + tolerance, y + tolerance))
    
    # ============ Statistics ============
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        if self._stats:
            return self._stats
            
        stats = {
            "total_strokes": len(self.strokes),
            "total_layers": len(self.layers),
            "total_groups": len(self.groups),
            "layers": {},
        }
        
        # Per-layer stats
        for layer_id, stroke_ids in self.layers.items():
            layer_strokes = [self.strokes[sid] for sid in stroke_ids if sid in self.strokes]
            stats["layers"][layer_id] = {
                "count": len(layer_strokes),
                "total_length": sum(s.get_length() for s in layer_strokes),
                "avg_width": np.mean([s.width for s in layer_strokes]) if layer_strokes else 0,
            }
        
        # Type distribution
        type_counts = defaultdict(int)
        for stroke in self.strokes.values():
            type_counts[stroke.type.value] += 1
        stats["type_distribution"] = dict(type_counts)
        
        self._stats = stats
        return stats
    
    # ============ Serialization ============
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "strokes": {sid: stroke.to_dict() for sid, stroke in self.strokes.items()},
            "stroke_order": self.stroke_order,
            "layers": self.layers,
            "groups": {gid: list(members) for gid, members in self.groups.items()},
            "dependencies": {aid: list(befores) for aid, befores in self.dependencies.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StrokeGraph:
        """Deserialize from dictionary."""
        graph = cls(id=data.get("id", f"graph_{uuid.uuid4().hex[:8]}"))
        
        # Restore strokes
        for sid, stroke_data in data.get("strokes", {}).items():
            graph.strokes[sid] = Stroke.from_dict(stroke_data)
            
        # Restore order
        graph.stroke_order = data.get("stroke_order", [])
        
        # Restore layers
        graph.layers = {k: list(v) for k, v in data.get("layers", {}).items()}
        
        # Restore groups
        graph.groups = {k: set(v) for k, v in data.get("groups", {}).items()}
        
        # Restore dependencies
        graph.dependencies = {k: set(v) for k, v in data.get("dependencies", {}).items()}
        
        # Rebuild spatial index
        for stroke_id in graph.strokes:
            graph._update_spatial_index(stroke_id)
            
        return graph
    
    def clone(self) -> StrokeGraph:
        """Create a deep copy."""
        return StrokeGraph.from_dict(self.to_dict())
