"""
I/O module - File format handling for .stroke files.

Defines the .stroke file format for storing complete painting information.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from dataclasses import asdict

from strokera.core.stroke import StrokeGraph
from strokera.core.canvas import Canvas


# File format version
STROKE_FORMAT_VERSION = "1.0"


class StrokeFile:
    """
    Handler for .stroke file format.
    
    The .stroke format is a structured archive containing:
    - manifest.json: Metadata and structure
    - graph.json: StrokeGraph serialization
    - canvas.json: Canvas state
    - brushes/: Brush definitions (if custom)
    - textures/: Texture images (if any)
    
    Files are stored as ZIP archives for portability.
    """
    
    def __init__(self):
        """Initialize the stroke file handler."""
        self.version = STROKE_FORMAT_VERSION
    
    def save(self, path: str | Path,
             stroke_graph: StrokeGraph,
             canvas: Canvas,
             include_pixels: bool = True) -> None:
        """
        Save a painting to .stroke format.
        
        Args:
            path: Output file path
            stroke_graph: The stroke graph to save
            canvas: The canvas state to save
            include_pixels: Whether to include layer pixels
        """
        path = Path(path)
        
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Write manifest
            manifest = {
                "version": self.version,
                "graph_id": stroke_graph.id,
                "canvas_width": canvas.width,
                "canvas_height": canvas.height,
                "include_pixels": include_pixels,
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            
            # Write stroke graph
            graph_data = stroke_graph.to_dict()
            zf.writestr("graph.json", json.dumps(graph_data, indent=2))
            
            # Write canvas
            canvas_data = canvas.to_dict()
            if not include_pixels:
                # Remove pixel data
                for layer_data in canvas_data.get("layers", {}).values():
                    layer_data.pop("pixels", None)
            zf.writestr("canvas.json", json.dumps(canvas_data, indent=2))
            
            # Write strokes data (separate for easy access)
            strokes_data = {
                "strokes": graph_data["strokes"],
                "stroke_order": graph_data["stroke_order"],
            }
            zf.writestr("strokes.json", json.dumps(strokes_data, indent=2))
            
            # Write layers data
            layers_data = {
                "layers": canvas_data["layers"],
                "active_layer_id": canvas_data["active_layer_id"],
            }
            zf.writestr("layers.json", json.dumps(layers_data, indent=2))
    
    def load(self, path: str | Path) -> Tuple[StrokeGraph, Dict[str, Any]]:
        """
        Load a painting from .stroke format.
        
        Args:
            path: Input file path
            
        Returns:
            Tuple of (StrokeGraph, canvas_dict)
        """
        path = Path(path)
        
        with zipfile.ZipFile(path, 'r') as zf:
            # Read manifest
            manifest = json.loads(zf.read("manifest.json").decode('utf-8'))
            
            # Read stroke graph
            graph_data = json.loads(zf.read("graph.json").decode('utf-8'))
            stroke_graph = StrokeGraph.from_dict(graph_data)
            
            # Read canvas
            canvas_data = json.loads(zf.read("canvas.json").decode('utf-8'))
            
            # Optionally read pixel data
            if manifest.get("include_pixels", True):
                # Pixel data is embedded in canvas.json layers
                pass
            
            return stroke_graph, canvas_data
    
    def load_graph(self, path: str | Path) -> StrokeGraph:
        """
        Load only the stroke graph (faster, no pixels).
        
        Args:
            path: Input file path
            
        Returns:
            StrokeGraph object
        """
        path = Path(path)
        
        with zipfile.ZipFile(path, 'r') as zf:
            graph_data = json.loads(zf.read("graph.json").decode('utf-8'))
            return StrokeGraph.from_dict(graph_data)
    
    def load_canvas(self, path: str | Path) -> Dict[str, Any]:
        """
        Load only the canvas data.
        
        Args:
            path: Input file path
            
        Returns:
            Canvas dictionary
        """
        path = Path(path)
        
        with zipfile.ZipFile(path, 'r') as zf:
            return json.loads(zf.read("canvas.json").decode('utf-8'))


class StrokeFileJSON:
    """
    Simple JSON-only stroke file handler.
    
    For cases where full pixel data is not needed.
    """
    
    @staticmethod
    def save(path: str | Path,
             stroke_graph: StrokeGraph,
             canvas: Canvas) -> None:
        """Save to simple JSON format."""
        data = {
            "version": STROKE_FORMAT_VERSION,
            "graph": stroke_graph.to_dict(),
            "canvas": canvas.to_dict(),
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def load(path: str | Path) -> Tuple[StrokeGraph, Dict[str, Any]]:
        """Load from simple JSON format."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = StrokeGraph.from_dict(data["graph"])
        canvas = data["canvas"]
        
        return graph, canvas


def validate_stroke_file(path: str | Path) -> Dict[str, Any]:
    """
    Validate a .stroke file and return info.
    
    Args:
        path: Path to validate
        
    Returns:
        Dictionary with validation results
    """
    path = Path(path)
    
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": {},
    }
    
    try:
        handler = StrokeFile()
        graph, canvas = handler.load(path)
        
        result["info"] = {
            "version": handler.version,
            "graph_id": graph.id,
            "num_strokes": len(graph.strokes),
            "num_layers": len(graph.layers),
            "canvas_width": canvas.get("width", 0),
            "canvas_height": canvas.get("height", 0),
        }
        
    except zipfile.BadZipFile:
        result["valid"] = False
        result["errors"].append("Not a valid ZIP archive")
    except KeyError as e:
        result["valid"] = False
        result["errors"].append(f"Missing required file: {e}")
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["errors"].append(f"Invalid JSON: {e}")
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Unknown error: {e}")
    
    return result
