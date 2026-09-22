"""
Strokera - Basic Tests

These tests verify the core functionality of the Strokera library.
"""

import pytest
import numpy as np

from strokera import (
    Stroke,
    StrokeGraph,
    StrokeType,
    Brush,
    BrushEngine,
    BrushType,
    Canvas,
    Layer,
    ImageAnalyzer,
    PaintingPlanner,
    StrokePlanner,
    AnalysisMode,
)


class TestStroke:
    """Tests for Stroke data structure."""
    
    def test_create_stroke(self):
        """Test basic stroke creation."""
        stroke = Stroke(
            path=[(0, 0), (100, 100)],
            width=10.0,
            color=(0.5, 0.3, 0.2),
            opacity=0.8,
        )
        
        assert stroke.width == 10.0
        assert stroke.color == (0.5, 0.3, 0.2)
        assert stroke.opacity == 0.8
        assert stroke.num_points == 2
    
    def test_add_point(self):
        """Test adding points to stroke."""
        stroke = Stroke()
        stroke.add_point(0, 0)
        stroke.add_point(50, 50)
        stroke.add_point(100, 100)
        
        assert stroke.num_points == 3
        assert len(stroke.path) == 3
    
    def test_get_bounding_box(self):
        """Test bounding box calculation."""
        stroke = Stroke(
            path=[(10, 20), (50, 80), (90, 30)]
        )
        
        bbox = stroke.get_bounding_box()
        assert bbox == (10, 20, 90, 80)
    
    def test_get_length(self):
        """Test stroke length calculation."""
        stroke = Stroke(
            path=[(0, 0), (100, 0), (100, 100)]  # L-shape
        )
        
        length = stroke.get_length()
        assert abs(length - 200) < 1  # 100 + 100
    
    def test_serialization(self):
        """Test stroke serialization to/from dict."""
        stroke = Stroke(
            type=StrokeType.PREDICTED,
            path=[(0, 0), (100, 100)],
            width=15.0,
            color=(1.0, 0.5, 0.0),
        )
        
        data = stroke.to_dict()
        restored = Stroke.from_dict(data)
        
        assert restored.id == stroke.id
        assert restored.width == stroke.width
        assert restored.color == stroke.color


class TestStrokeGraph:
    """Tests for StrokeGraph."""
    
    def test_create_graph(self):
        """Test graph creation."""
        graph = StrokeGraph()
        assert len(graph.strokes) == 0
        assert len(graph.layers) == 1  # Default layer
    
    def test_add_stroke(self):
        """Test adding stroke to graph."""
        graph = StrokeGraph()
        stroke = Stroke(path=[(0, 0), (100, 100)])
        
        stroke_id = graph.add_stroke(stroke)
        
        assert stroke_id == stroke.id
        assert stroke_id in graph.strokes
        assert stroke_id in graph.stroke_order
    
    def test_layer_management(self):
        """Test layer operations."""
        graph = StrokeGraph()
        
        # Add a layer
        graph.add_layer("foreground")
        assert "foreground" in graph.layers
        
        # Add stroke to layer
        stroke = Stroke(path=[(0, 0), (100, 100)])
        graph.add_stroke(stroke, layer_id="foreground")
        
        assert stroke.id in graph.layers["foreground"]
    
    def test_get_strokes_in_order(self):
        """Test ordered iteration."""
        graph = StrokeGraph()
        
        for i in range(5):
            stroke = Stroke(path=[(i*10, 0), (i*10+10, 10)])
            graph.add_stroke(stroke)
        
        strokes = list(graph.get_strokes_in_order())
        assert len(strokes) == 5
        assert strokes[0].render_order == 0
        assert strokes[-1].render_order == 4
    
    def test_serialization(self):
        """Test graph serialization."""
        graph = StrokeGraph()
        
        for i in range(3):
            stroke = Stroke(path=[(i*10, 0), (i*10+10, 10)])
            graph.add_stroke(stroke)
        
        data = graph.to_dict()
        restored = StrokeGraph.from_dict(data)
        
        assert len(restored.strokes) == 3


class TestBrush:
    """Tests for Brush system."""
    
    def test_create_brush(self):
        """Test brush creation."""
        brush = Brush(
            name="Test Brush",
            type=BrushType.OIL,
            base_width=20.0,
        )
        
        assert brush.name == "Test Brush"
        assert brush.type == BrushType.OIL
        assert brush.base_width == 20.0
    
    def test_preset_brush(self):
        """Test brush presets."""
        oil_brush = Brush.create_preset("oil_round")
        
        assert oil_brush.name == "Oil Round"
        assert oil_brush.type == BrushType.OIL
        assert oil_brush.base_width == 20.0
    
    def test_watercolor_preset(self):
        """Test watercolor preset."""
        brush = Brush.create_preset("watercolor")
        
        assert brush.type == BrushType.WATERCOLOR
        assert brush.wet_spread > 0


class TestCanvas:
    """Tests for Canvas."""
    
    def test_create_canvas(self):
        """Test canvas creation."""
        canvas = Canvas(1024, 768)
        
        assert canvas.width == 1024
        assert canvas.height == 768
        assert len(canvas.layers) == 1  # Default layer
    
    def test_add_layer(self):
        """Test layer management."""
        canvas = Canvas(512, 512)
        
        layer = canvas.add_layer("new_layer")
        
        assert layer.name == "new_layer"
        assert "new_layer" in canvas.layers
    
    def test_render(self):
        """Test canvas rendering."""
        canvas = Canvas(100, 100, background=(255, 255, 255))
        result = canvas.render()
        
        assert result.shape == (100, 100, 3)
        assert result[50, 50, 0] == 255  # White background


class TestImageAnalyzer:
    """Tests for ImageAnalyzer."""
    
    def test_create_analyzer(self):
        """Test analyzer creation."""
        analyzer = ImageAnalyzer()
        assert analyzer is not None
    
    def test_analyze_synthetic_image(self):
        """Test analyzing a synthetic image."""
        analyzer = ImageAnalyzer()
        
        # Create a simple test image
        image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        
        result = analyzer.analyze(image, mode=AnalysisMode.FAST)
        
        assert result.width == 256
        assert result.height == 256
        assert result.edges is not None


class TestPaintingPlanner:
    """Tests for PaintingPlanner."""
    
    def test_create_planner(self):
        """Test planner creation."""
        planner = PaintingPlanner()
        assert planner is not None
    
    def test_default_plan(self):
        """Test creating a default plan."""
        planner = PaintingPlanner()
        
        # Create mock analysis result
        from strokera.planning import Segment
        from strokera.planning.image_analyzer import AnalysisResult
        
        analysis = AnalysisResult(width=1024, height=1024)
        analysis.segments["seg1"] = Segment(
            label="test",
            bbox=(100, 100, 200, 200),
            area=40000,
            mean_color=(0.5, 0.3, 0.2),
        )
        
        plan = planner.plan(analysis, target_strokes=100)
        
        assert plan.canvas_width == 1024
        assert plan.total_strokes_target == 100
        assert len(plan.layers) > 0


class TestStrokePlanner:
    """Tests for StrokePlanner."""
    
    def test_create_planner(self):
        """Test stroke planner creation."""
        planner = StrokePlanner()
        assert planner is not None
    
    def test_generate_strokes(self):
        """Test stroke generation."""
        from strokera.planning import PaintingPlan, PaintRegion
        
        planner = StrokePlanner()
        
        # Create a simple plan
        plan = PaintingPlan(
            canvas_width=256,
            canvas_height=256,
            total_strokes_target=10,
        )
        
        # Add a region
        region = PaintRegion(
            bbox=(0, 0, 1, 1),  # Full canvas
            target_color=(0.5, 0.5, 0.5),
            stroke_width_base=10,
        )
        plan.regions[region.id] = region
        
        # Create a layer
        from strokera.planning import PaintLayer, PaintLayerType
        layer = PaintLayer(
            type=PaintLayerType.BACKGROUND,
            name="Test",
            regions=[region.id],
        )
        layer.metadata["stroke_budget"] = 10
        plan.layers["test"] = layer
        plan.layer_order = ["test"]
        
        # Generate strokes
        graph = planner.plan(plan)
        
        assert len(graph.strokes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
