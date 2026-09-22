"""
Image Analyzer - Analyzes input images for semantic understanding.

Performs:
- Semantic segmentation
- Depth estimation
- Edge detection
- Normal estimation
- Color analysis
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any, Callable
from pathlib import Path
import numpy as np
from numpy.typing import NDArray

# Optional imports - these are loaded lazily
_has_cv2 = False
_has_torch = False

try:
    import cv2
    _has_cv2 = True
except ImportError:
    pass

try:
    import torch
    import torchvision.transforms as transforms
    _has_torch = True
except ImportError:
    pass


class AnalysisMode(Enum):
    """What level of analysis to perform."""
    FAST = "fast"           # Edges only
    STANDARD = "standard"   # Edges + basic segmentation
    FULL = "full"           # Everything including depth/normals


@dataclass
class Segment:
    """
    A segmented region in the image.
    
    Represents a coherent region with shared semantic properties.
    """
    id: str = field(default_factory=lambda: f"seg_{uuid.uuid4().hex[:8]}")
    label: str = "unknown"
    
    # Mask
    mask: Optional[NDArray[np.bool_]] = None  # Binary mask
    
    # Properties
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h
    area: float = 0.0
    
    # Color statistics
    mean_color: Tuple[float, float, float] = (0, 0, 0)
    dominant_color: Tuple[float, float, float] = (0, 0, 0)
    
    # Position and depth
    center: Tuple[float, float] = (0, 0)
    depth: Optional[float] = None
    
    # Importance (for painting priority)
    importance: float = 0.5
    
    # Nested segments
    children: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "label": self.label,
            "bbox": self.bbox,
            "area": self.area,
            "mean_color": list(self.mean_color),
            "dominant_color": list(self.dominant_color),
            "center": list(self.center),
            "depth": self.depth,
            "importance": self.importance,
            "children": self.children,
            "parent_id": self.parent_id,
        }


@dataclass
class AnalysisResult:
    """
    Complete analysis result of an input image.
    
    Contains all extracted information about the image.
    """
    
    id: str = field(default_factory=lambda: f"analysis_{uuid.uuid4().hex[:8]}")
    
    # Image properties
    width: int = 0
    height: int = 0
    
    # Edge detection
    edges: Optional[NDArray[np.float32]] = None
    edge_strength: float = 0.0
    
    # Depth map (if available)
    depth_map: Optional[NDArray[np.float32]] = None
    
    # Normal map (if available)
    normal_map: Optional[NDArray[np.float32]] = None
    
    # Segments
    segments: Dict[str, Segment] = field(default_factory=dict)
    segment_mask: Optional[NDArray[np.int32]] = None
    
    # Color analysis
    color_palette: List[Tuple[float, float, float]] = field(default_factory=list)
    color_histogram: Optional[NDArray[np.float32]] = None
    
    # Composition
    saliency_map: Optional[NDArray[np.float32]] = None
    focal_points: List[Tuple[float, float, float]] = field(default_factory=list)  # x, y, strength
    
    # Composition lines
    composition_lines: List[Tuple[Tuple[float, float], Tuple[float, float]]] = field(default_factory=list)
    
    # Metadata
    mode: AnalysisMode = AnalysisMode.STANDARD
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_segments_sorted(self, by: str = "importance") -> List[Segment]:
        """Get segments sorted by a property."""
        segs = list(self.segments.values())
        if by == "importance":
            return sorted(segs, key=lambda s: s.importance, reverse=True)
        elif by == "area":
            return sorted(segs, key=lambda s: s.area, reverse=True)
        elif by == "depth":
            return sorted(segs, key=lambda s: s.depth or 0.0)
        return segs
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "width": self.width,
            "height": self.height,
            "edge_strength": self.edge_strength,
            "segments": {sid: seg.to_dict() for sid, seg in self.segments.items()},
            "color_palette": [list(c) for c in self.color_palette],
            "focal_points": [list(fp) for fp in self.focal_points],
            "composition_lines": [[list(p1), list(p2)] for p1, p2 in self.composition_lines],
            "mode": self.mode.value,
            "processing_time": self.processing_time,
            "metadata": self.metadata,
        }


class ImageAnalyzer:
    """
    Analyzes images to extract semantic information.
    
    This class provides various analysis methods:
    - Edge detection (Canny, Sobel, etc.)
    - Segmentation (SLIC, Felzenszwalb, etc.)
    - Depth estimation (if models available)
    - Color analysis
    
    Usage:
        analyzer = ImageAnalyzer()
        result = analyzer.analyze(image_path, mode=AnalysisMode.FULL)
    """
    
    def __init__(self, device: str = "cpu"):
        """
        Initialize the analyzer.
        
        Args:
            device: Device for neural network inference ("cpu" or "cuda")
        """
        self.device = device
        self._segmentation_model = None
        self._depth_model = None
        self._normal_model = None
        
    def analyze(self, image_path: str | Path | NDArray[np.uint8],
                mode: AnalysisMode = AnalysisMode.STANDARD) -> AnalysisResult:
        """
        Analyze an image.
        
        Args:
            image_path: Path to image or numpy array
            mode: Level of analysis detail
            
        Returns:
            AnalysisResult with all extracted information
        """
        import time
        start_time = time.time()
        
        # Load image
        if isinstance(image_path, (str, Path)):
            image = self._load_image(image_path)
        else:
            image = image_path
            
        result = AnalysisResult(
            width=image.shape[1],
            height=image.shape[0],
            mode=mode,
        )
        
        # Always do edge detection
        result.edges, result.edge_strength = self._detect_edges(image)
        
        if mode.value in ("standard", "full"):
            # Segmentation
            result.segments, result.segment_mask = self._segment_image(image)
            
            # Color analysis
            result.color_palette = self._extract_color_palette(image, num_colors=8)
            
        if mode.value == "full":
            # Depth estimation
            result.depth_map = self._estimate_depth(image)
            
            # Normal estimation
            result.normal_map = self._estimate_normals(image)
            
            # Saliency
            result.saliency_map, result.focal_points = self._compute_saliency(image)
            
        result.processing_time = time.time() - start_time
        return result
    
    def _load_image(self, path: str | Path) -> NDArray[np.uint8]:
        """Load image from path."""
        if _has_cv2:
            img = cv2.imread(str(path))
            if img is not None:
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Fallback to PIL
        from PIL import Image
        img = Image.open(path)
        return np.array(img)
    
    def _detect_edges(self, image: NDArray[np.uint8]) -> Tuple[NDArray[np.float32], float]:
        """
        Detect edges in the image.
        
        Returns:
            Tuple of (edge_map, edge_strength)
        """
        if _has_cv2:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
                
            # Apply Canny edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Calculate strength
            edge_strength = edges.sum() / (edges.shape[0] * edges.shape[1] * 255)
            
            return edges.astype(np.float32), edge_strength
        else:
            # Simple fallback using numpy
            if len(image.shape) == 3:
                gray = np.mean(image, axis=2)
            else:
                gray = image
                
            # Sobel-like edge detection
            kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
            kernel_y = kernel_x.T
            
            from scipy.ndimage import convolve
            gx = convolve(gray.astype(float), kernel_x)
            gy = convolve(gray.astype(float), kernel_y)
            edges = np.sqrt(gx**2 + gy**2)
            
            edge_strength = edges.sum() / (edges.shape[0] * edges.shape[1] * 255)
            
            return (edges / 255.0).astype(np.float32), edge_strength
    
    def _segment_image(self, image: NDArray[np.uint8]) -> Tuple[Dict[str, Segment], Optional[NDArray[np.int32]]]:
        """
        Segment the image into coherent regions.
        
        Returns:
            Tuple of (segments_dict, segment_mask)
        """
        if _has_cv2:
            # Use SLIC superpixels
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
                
            # SLIC segmentation
            if hasattr(cv2, 'ximgproc'):
                try:
                    # OpenCV has SLIC in ximgproc
                    segments = cv2.ximgproc.createSuperpixelSLIC(gray, method="SLIC")
                    segments.iterate(num_iterations=10)
                    
                    mask = segments.getLabelContourMask()
                    labels = segments.getLabels()
                except:
                    # Fallback to Felzenszwalb
                    labels = self._felzenszwalb_segmentation(gray)
                    mask = None
            else:
                labels = self._felzenszwalb_segmentation(gray)
                mask = None
        else:
            labels = self._felzenszwalb_segmentation(image)
            mask = None
        
        # Convert to Segment objects
        segments_dict = self._labels_to_segments(labels, image)
        
        return segments_dict, labels
    
    def _felzenszwalb_segmentation(self, image: NDArray[np.uint8]) -> NDArray[np.int32]:
        """Simple Felzenszwalb-style segmentation using numpy."""
        if len(image.shape) == 3:
            # Color image
            from scipy.ndimage import label
            
            # Simple threshold-based regions
            small_image = image[:, :, 0].astype(np.int32) // 32 * 32 + \
                         image[:, :, 1].astype(np.int32) // 32 * 32 + \
                         image[:, :, 2].astype(np.int32) // 32 * 32
            
            labels, num = label(small_image)
            return labels.astype(np.int32)
        else:
            from scipy.ndimage import label
            labels, num = label(image // 32)
            return labels.astype(np.int32)
    
    def _labels_to_segments(self, labels: NDArray[np.int32], 
                            image: NDArray[np.uint8]) -> Dict[str, Segment]:
        """Convert label map to Segment objects."""
        segments = {}
        
        unique_labels = np.unique(labels)
        
        for label_id in unique_labels:
            mask = labels == label_id
            
            # Calculate bbox
            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            if not rows.any() or not cols.any():
                continue
                
            y_min, y_max = np.where(rows)[0][[0, -1]]
            x_min, x_max = np.where(cols)[0][[0, -1]]
            
            # Calculate center
            center_y = (y_min + y_max) / 2
            center_x = (x_min + x_max) / 2
            
            # Color statistics
            region_pixels = image[mask]
            mean_color = np.mean(region_pixels, axis=0) / 255.0
            
            # Simple label based on color
            label_name = self._classify_region(mean_color)
            
            segment = Segment(
                label=label_name,
                mask=mask,
                bbox=(x_min, y_min, x_max - x_min, y_max - y_min),
                area=mask.sum(),
                mean_color=tuple(mean_color[:3]),
                dominant_color=tuple(mean_color[:3]),
                center=(center_x, center_y),
                importance=self._calculate_importance(mask, mean_color),
            )
            
            segments[segment.id] = segment
            
        return segments
    
    def _classify_region(self, color: Tuple[float, float, float]) -> str:
        """Classify a region based on its color."""
        r, g, b = color
        
        # Simple heuristics
        brightness = (r + g + b) / 3
        
        if brightness > 0.85:
            return "highlight"
        elif brightness < 0.15:
            return "shadow"
        elif r > g and r > b and g < 0.4:
            return "skin" if 0.2 < g < 0.5 else "red_object"
        elif b > r and b > g:
            return "sky" if brightness > 0.4 else "blue_object"
        elif g > r and g > b:
            return "foliage" if brightness > 0.3 else "green_object"
        elif brightness < 0.3:
            return "dark"
        else:
            return "neutral"
    
    def _calculate_importance(self, mask: NDArray[np.bool_], 
                             color: Tuple[float, float, float]) -> float:
        """Calculate painting importance of a region."""
        # Edge regions are more important
        # Large contiguous regions are less important
        
        area = mask.sum()
        importance = min(1.0, area / 10000)  # Normalize by typical image size
        
        # Boost for edge-adjacent regions
        from scipy.ndimage import binary_dilation
        dilated = binary_dilation(mask, iterations=3)
        edge_adjacent = dilated ^ mask
        importance *= 1.0 + 0.2 * edge_adjacent.sum() / max(area, 1)
        
        return min(1.0, importance)
    
    def _extract_color_palette(self, image: NDArray[np.uint8], 
                              num_colors: int = 8) -> List[Tuple[float, float, float]]:
        """Extract dominant colors from image."""
        # Simple quantization-based extraction
        pixels = image.reshape(-1, 3)
        
        # Simple k-means-like quantization
        step = 256 // 8
        quantized = (pixels // step) * step + step // 2
        
        # Count occurrences
        from collections import Counter
        counts = Counter(map(tuple, quantized))
        
        # Get top colors
        top_colors = counts.most_common(num_colors)
        
        return [(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0) 
                for c, _ in top_colors]
    
    def _estimate_depth(self, image: NDArray[np.uint8]) -> Optional[NDArray[np.float32]]:
        """Estimate depth map (requires neural network)."""
        if not _has_torch:
            return None
            
        # Load depth estimation model if available
        # This would use MiDaS or similar
        # For now, return None (not implemented)
        return None
    
    def _estimate_normals(self, image: NDArray[np.uint8]) -> Optional[NDArray[np.float32]]:
        """Estimate surface normals (requires neural network)."""
        if not _has_torch:
            return None
        return None
    
    def _compute_saliency(self, image: NDArray[np.uint8]) -> Tuple[Optional[NDArray[np.float32]], List]:
        """Compute saliency map and focal points."""
        if _has_cv2:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
                
            # Simple saliency using frequency domain
            fft = np.fft.fft2(gray)
            magnitude = np.abs(np.fft.fftshift(fft))
            
            # Gaussian blur on magnitude
            from scipy.ndimage import gaussian_filter
            log_magnitude = np.log1p(magnitude)
            saliency = gaussian_filter(log_magnitude, sigma=20)
            
            # Normalize
            saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min() + 1e-8)
            
            # Find focal points (local maxima)
            from scipy.ndimage import maximum_filter
            local_max = maximum_filter(saliency, size=50) == saliency
            peaks = np.where(local_max & (saliency > 0.5))
            
            focal_points = [(float(x), float(y), float(saliency[y, x])) 
                           for y, x in zip(peaks[0], peaks[1])]
            
            return saliency.astype(np.float32), focal_points
            
        return None, []
    
    def to_dict(self, result: AnalysisResult) -> Dict[str, Any]:
        """Serialize analysis result to dictionary."""
        return result.to_dict()
