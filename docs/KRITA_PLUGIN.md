# Krita Plugin Architecture

**Status:** Planned (v0.3)  
**This document describes the planned Krita integration.**

---

## Overview

The Strokera Krita plugin enables professional artists to use stroke-based AI painting directly within Krita's interface. The painting process is visible stroke-by-stroke on the canvas.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         KRITA                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐                                        │
│  │  Strokera Dock  │  ← Artist controls parameters          │
│  │  ┌───────────┐  │                                        │
│  │  │ Strokes:  │  │                                        │
│  │  │ Strategy: │  │                                        │
│  │  │ Brush:    │  │                                        │
│  │  │ [Paint]   │  │                                        │
│  │  └───────────┘  │                                        │
│  └────────┬────────┘                                        │
│           │                                                   │
│           │ REST API / WebSocket                             │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────┐        │
│  │            Strokera Backend                     │        │
│  │  ┌──────────────┐  ┌──────────────┐            │        │
│  │  │   Planner    │  │   Optimizer  │            │        │
│  │  └──────────────┘  └──────────────┘            │        │
│  │           │                  │                   │        │
│  │           ▼                  ▼                   │        │
│  │  ┌──────────────────────────────────────┐       │        │
│  │  │         Stroke Stream                 │       │        │
│  │  │  stroke #001 → stroke #002 → ...     │       │        │
│  │  └──────────────────────────────────────┘       │        │
│  └─────────────────────────────────────────────────┘        │
│                         │                                   │
│           WebSocket Stream                                  │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────────┐        │
│  │            Krita Canvas                          │        │
│  │                                                  │        │
│  │   [Watching stroke #001 appear...]              │        │
│  │   [stroke #002...]                              │        │
│  │   [stroke #003...]                              │        │
│  │   ...                                           │        │
│  │                                                  │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Krita Plugin (Python/PyQt)

```
krita-plugin/
├── __init__.py              # Plugin entry point
├── strokera_dock.py         # Dock widget with UI
├── strokera_server.py       # Local backend controller
├── stroke_renderer.py       # Real-time stroke display
└── settings.py              # Configuration
```

**Key Classes:**

```python
class StrokeraDock(DockWidget):
    """Main dock widget for Strokera controls."""
    
    def __init__(self):
        super().__init__()
        self.server = StrokeraServer()
        self.ui = StrokeraUI()
        
    def paint(self, image_path, strokes, strategy):
        """Start painting process."""
        self.server.start_painting(image_path, strokes, strategy)
        
    def on_stroke_ready(self, stroke_data):
        """Callback when a stroke is ready to render."""
        self.stroke_renderer.add_stroke(stroke_data)
```

### 2. Backend Server (Python)

```
backend/
├── server.py                 # Flask/FastAPI server
├── websocket_handler.py      # Real-time stroke streaming
├── planner.py               # Painting planner integration
├── optimizer.py            # Stroke optimizer integration
└── models/                  # ML models
```

**API Endpoints:**

```
POST /api/paint
    Body: {
        "image": "base64...",
        "strokes": 1000,
        "strategy": "auto",
        "brush": "oil_round"
    }
    Response: { "session_id": "..." }

GET /api/status/{session_id}
    Response: {
        "strokes_total": 1000,
        "strokes_completed": 456,
        "current_stroke": {...}
    }

WebSocket /ws/strokes/{session_id}
    Messages: {
        "type": "stroke",
        "data": {
            "id": "stroke_001",
            "path": [...],
            "color": [...],
            "width": 12.5
        }
    }
```

### 3. Real-time Stroke Renderer

The renderer listens to WebSocket and draws strokes on Krita's canvas in real-time.

```python
class StrokeRenderer:
    """Renders strokes in real-time on Krita canvas."""
    
    def __init__(self, view):
        self.view = view
        self.undo_group = KUndo2Command("Strokera Painting")
        
    def add_stroke(self, stroke_data):
        """Add a stroke to the canvas."""
        path = self.create_krita_path(stroke_data)
        brush = self.create_brush(stroke_data)
        
        # Paint stroke
        self.view.paintDevice().paintPath(path, brush)
        
        # Update progress
        self.update_progress(len(self.strokes))
```

## User Workflow

1. **Artist opens image** in Krita
2. **Opens Strokera dock** (View → Dockers → Strokera)
3. **Configures settings:**
   - Number of strokes (500 - 50000)
   - Strategy (Auto, Portrait, Landscape)
   - Brush type (Oil, Watercolor, etc.)
4. **Clicks "Paint"**
5. **Watches strokes appear** stroke-by-stroke on canvas
6. **Can cancel** at any time
7. **Continues editing** once complete

## Progress Indication

```
┌─────────────────────────────────────┐
│ Strokera                            │
├─────────────────────────────────────┤
│ Strokes: 5,000 / 50,000             │
│ ████████████░░░░░░░░░░░░░  10%      │
│                                     │
│ Current: Layer 2 - Foreground       │
│ Stroke: #4,892 / 50,000            │
│                                     │
│ [███████░░░░░░░░░░░░░░░░░░]        │
│                                     │
│ [    Paint    ] [  Cancel  ]        │
└─────────────────────────────────────┘
```

## Installation

### Requirements

- Krita 5.0+
- Python 3.10+
- Strokera package installed
- (Optional) CUDA for GPU acceleration

### Installation Steps

```bash
# 1. Install Strokera
pip install strokera[gpu]

# 2. Copy plugin to Krita's python plugins directory
# Linux/macOS:
cp -r krita-plugin ~/.local/share/krita/pykrita/

# Windows:
# Copy to %APPDATA%\krita\pykrita\

# 3. Restart Krita
# 4. Enable in Settings → Configure Krita → Python Plugin Manager
```

## Technical Considerations

### WebSocket Protocol

Strokes are streamed as JSON messages:

```json
{
    "type": "stroke",
    "session_id": "abc123",
    "stroke": {
        "id": "stroke_0042",
        "layer": "foreground",
        "path": [[100, 200], [150, 220], ...],
        "color": [0.23, 0.18, 0.12],
        "width": 12.5,
        "opacity": 0.85
    },
    "progress": {
        "current": 42,
        "total": 5000,
        "percent": 0.84
    }
}
```

### Performance

- Strokes are generated in batches (configurable, default 50)
- Each batch is streamed immediately when ready
- Krita renders strokes in real-time using the vector engine
- Undo history is maintained for full undo support

### Memory Management

- Backend keeps full StrokeGraph in memory
- Krita plugin only keeps visible strokes
- Older strokes can be flattened if needed
- Session can be saved as `.stroke` file at any time

## Future Enhancements

- [ ] Progressive preview (low-res → high-res refinement)
- [ ] Interactive editing during generation
- [ ] Multiple brush types in single painting
- [ ] Custom brush training
- [ ] Style transfer between paintings
