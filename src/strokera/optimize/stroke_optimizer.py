"""
Stroke Optimizer - Optimizes stroke parameters using differentiable rendering.

Based on diffvg (Differentiable Vector Graphics): optimizes stroke parameters
by comparing rendered output with target image.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Callable, TYPE_CHECKING
import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    import torch

from strokera.core.stroke import Stroke, StrokeGraph


class DifferentiableRenderer:
    """
    Wrapper for differentiable rendering (diffvg).
    
    Provides forward and backward passes for stroke rendering,
    enabling gradient-based optimization.
    """
    
    def __init__(self, device: str = "cpu"):
        """
        Initialize the differentiable renderer.
        
        Args:
            device: Device for computation ("cpu" or "cuda")
        """
        self.device = device
        self._diffvg_available = False
        self._torch = None
        self._try_load_diffvg()
    
    def _try_load_diffvg(self) -> bool:
        """Try to load diffvg library."""
        try:
            import torch
            import diffvg
            self._torch = torch
            self._diffvg_available = True
            return True
        except ImportError:
            self._diffvg_available = False
            return False
    
    @property
    def is_available(self) -> bool:
        """Check if diffvg is available."""
        return self._diffvg_available
    
    def render_stroke(self, stroke: Stroke,
                      width: int, height: int) -> NDArray[np.float32]:
        """
        Render a stroke to an image.
        
        Args:
            stroke: Stroke to render
            width: Canvas width
            height: Canvas height
            
        Returns:
            Rendered image as float32 array
        """
        if not self._diffvg_available:
            return self._fallback_render(stroke, width, height)
        
        import torch
        
        # Convert stroke to diffvg format
        num_points = len(stroke.path)
        if num_points < 2:
            return np.zeros((height, width, 3), dtype=np.float32)
        
        # Build path points
        points = []
        for x, y in stroke.path:
            points.append([x / width, y / height])  # Normalize to [0, 1]
        
        # Create path
        path = self._create_diffvg_path(points)
        
        # Set fill/stroke
        stroke_color = torch.tensor(
            [*stroke.color, stroke.opacity],
            device=self.device,
        )
        
        # Render
        scene = torch.zeros(3, height, width, device=self.device)
        # Note: actual diffvg rendering would go here
        # This is a placeholder
        
        return scene.cpu().numpy().transpose(1, 2, 0)
    
    def _create_diffvg_path(self, points: List[List[float]]):
        """Create a diffvg path from points."""
        import diffvg
        num_segments = len(points) - 1
        points_tensor = torch.tensor(
            points, dtype=torch.float32, device=self.device
        ).unsqueeze(0)
        
        path = diffvg.Path(
            num_control_points=torch.zeros(num_segments, dtype=torch.int32) + 2,
            points=points_tensor,
            is_closed=False,
        )
        return path
    
    def _fallback_render(self, stroke: Stroke,
                         width: int, height: int) -> NDArray[np.float32]:
        """Fallback rendering without diffvg."""
        img = np.zeros((height, width, 3), dtype=np.float32)
        
        if len(stroke.path) < 2:
            return img
        
        # Simple line rendering
        from strokera.core.brush import BrushEngine
        
        # Convert to simple format for BrushEngine
        stroke_copy = stroke.clone()
        
        return img


@dataclass
class OptimizationConfig:
    """Configuration for stroke optimization."""
    
    # Learning rate
    learning_rate: float = 0.01
    
    # Number of iterations
    iterations: int = 100
    
    # Which parameters to optimize
    optimize_position: bool = True
    optimize_width: bool = True
    optimize_color: bool = True
    optimize_path: bool = False  # More expensive
    
    # Loss function weights
    pixel_loss_weight: float = 1.0
    perceptual_loss_weight: float = 0.1
    smoothness_loss_weight: float = 0.01
    
    # Convergence
    early_stopping_patience: int = 10
    early_stopping_threshold: float = 1e-4
    
    # Progress
    verbose: bool = True
    log_interval: int = 10


@dataclass
class OptimizationResult:
    """Result of stroke optimization."""
    
    # Initial and final losses
    initial_loss: float = 0.0
    final_loss: float = 0.0
    
    # Per-iteration losses
    loss_history: List[float] = field(default_factory=list)
    
    # Optimized strokes
    optimized_strokes: List[Stroke] = field(default_factory=list)
    
    # Statistics
    iterations_run: int = 0
    converged: bool = False
    improvement: float = 0.0
    
    # Timing
    total_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "initial_loss": self.initial_loss,
            "final_loss": self.final_loss,
            "loss_history": self.loss_history,
            "optimized_strokes": [s.to_dict() for s in self.optimized_strokes],
            "iterations_run": self.iterations_run,
            "converged": self.converged,
            "improvement": self.improvement,
            "total_time": self.total_time,
        }


class StrokeOptimizer:
    """
    Optimizes stroke parameters to minimize rendering error.
    
    Uses differentiable rendering (diffvg) to compute gradients
    and update stroke parameters.
    
    The optimization process:
    1. Render current strokes to canvas
    2. Compare with target image
    3. Compute loss
    4. Backpropagate to stroke parameters
    5. Update parameters
    6. Repeat
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None,
                 renderer: Optional[DifferentiableRenderer] = None):
        """
        Initialize the optimizer.
        
        Args:
            config: Optimization configuration
            renderer: Differentiable renderer (creates one if None)
        """
        self.config = config or OptimizationConfig()
        self.renderer = renderer or DifferentiableRenderer()
    
    def optimize(self, strokes: List[Stroke],
                 target_image: NDArray[np.uint8],
                 progress_callback: Optional[Callable[[int, float], None]] = None,
                 ) -> OptimizationResult:
        """
        Optimize strokes to match target image.
        
        Args:
            strokes: Initial strokes
            target_image: Target image to match
            progress_callback: Optional callback(iter, loss)
            
        Returns:
            OptimizationResult with optimized strokes
        """
        import time
        start_time = time.time()
        
        result = OptimizationResult()
        
        if not self.renderer.is_available:
            # Fallback: return original strokes with no optimization
            result.optimized_strokes = [s.clone() for s in strokes]
            result.final_loss = float('inf')
            result.total_time = time.time() - start_time
            return result
        
        # Normalize target image
        if len(target_image.shape) == 3 and target_image.shape[2] == 3:
            target = target_image.astype(np.float32) / 255.0
        else:
            target = target_image.astype(np.float32) / 255.0
            if len(target.shape) == 2:
                target = np.stack([target] * 3, axis=-1)
        
        height, width = target.shape[:2]
        
        # Setup PyTorch tensors for optimization
        import torch
        
        # Initialize stroke parameter tensors
        stroke_params = self._setup_stroke_tensors(strokes)
        
        # Optimizer
        optimizer = torch.optim.Adam(
            stroke_params.values(),
            lr=self.config.learning_rate,
        )
        
        # Target tensor
        target_tensor = torch.from_numpy(target).to(self.renderer.device)
        
        best_loss = float('inf')
        patience_counter = 0
        
        for iteration in range(self.config.iterations):
            optimizer.zero_grad()
            
            # Render strokes
            rendered = self._render_strokes_torch(
                stroke_params, strokes, width, height
            )
            
            # Compute loss
            loss = self._compute_loss(rendered, target_tensor)
            
            # Backpropagate
            loss.backward()
            optimizer.step()
            
            loss_value = loss.item()
            result.loss_history.append(loss_value)
            
            # Early stopping check
            if loss_value < best_loss - self.config.early_stopping_threshold:
                best_loss = loss_value
                patience_counter = 0
            else:
                patience_counter += 1
                
            if patience_counter >= self.config.early_stopping_patience:
                result.converged = True
                break
            
            # Progress callback
            if progress_callback:
                progress_callback(iteration + 1, loss_value)
            
            # Logging
            if self.config.verbose and iteration % self.config.log_interval == 0:
                print(f"Iteration {iteration + 1}: loss = {loss_value:.6f}")
        
        # Final result
        result.initial_loss = result.loss_history[0] if result.loss_history else 0
        result.final_loss = result.loss_history[-1] if result.loss_history else 0
        result.iterations_run = len(result.loss_history)
        result.improvement = result.initial_loss - result.final_loss
        
        # Extract optimized strokes
        result.optimized_strokes = self._extract_optimized_strokes(
            stroke_params, strokes
        )
        
        result.total_time = time.time() - start_time
        
        return result
    
    def _setup_stroke_tensors(self, strokes: List[Stroke]) -> Dict[str, torch.Tensor]:
        """Setup PyTorch tensors for stroke parameters."""
        import torch
        
        params = {}
        
        for i, stroke in enumerate(strokes):
            prefix = f"stroke_{i}_"
            
            if self.config.optimize_position:
                # Calculate stroke center
                if stroke.path:
                    xs = [p[0] for p in stroke.path]
                    ys = [p[1] for p in stroke.path]
                    center_x = sum(xs) / len(xs)
                    center_y = sum(ys) / len(ys)
                    params[prefix + "cx"] = torch.tensor(
                        [center_x], requires_grad=True, device=self.renderer.device
                    )
                    params[prefix + "cy"] = torch.tensor(
                        [center_y], requires_grad=True, device=self.renderer.device
                    )
            
            if self.config.optimize_width:
                params[prefix + "width"] = torch.tensor(
                    [stroke.width], requires_grad=True, device=self.renderer.device
                )
            
            if self.config.optimize_color:
                params[prefix + "color"] = torch.tensor(
                    list(stroke.color), requires_grad=True, device=self.renderer.device
                )
        
        return params
    
    def _render_strokes_torch(self, params: Dict[str, torch.Tensor],
                              strokes: List[Stroke],
                              width: int, height: int) -> torch.Tensor:
        """Render strokes using PyTorch (for differentiable rendering)."""
        import torch
        
        # Placeholder: actual implementation would use diffvg
        rendered = torch.zeros(3, height, width, device=self.renderer.device)
        
        return rendered
    
    def _compute_loss(self, rendered: torch.Tensor, 
                     target: torch.Tensor) -> torch.Tensor:
        """Compute loss between rendered and target."""
        import torch
        
        # MSE loss
        pixel_loss = torch.mean((rendered - target) ** 2)
        
        # Total loss with weights
        total_loss = (
            self.config.pixel_loss_weight * pixel_loss +
            self.config.perceptual_loss_weight * 0 +  # Placeholder
            self.config.smoothness_loss_weight * 0     # Placeholder
        )
        
        return total_loss
    
    def _extract_optimized_strokes(self, params: Dict[str, torch.Tensor],
                                  original_strokes: List[Stroke]) -> List[Stroke]:
        """Extract optimized stroke parameters."""
        import torch
        
        optimized = []
        
        for i, stroke in enumerate(original_strokes):
            new_stroke = stroke.clone()
            prefix = f"stroke_{i}_"
            
            # Update position
            if prefix + "cx" in params:
                offset_x = params[prefix + "cx"].item() - stroke.path[0][0]
                offset_y = params[prefix + "cy"].item() - stroke.path[0][1]
                
                new_path = []
                for x, y in stroke.path:
                    new_path.append((x + offset_x, y + offset_y))
                new_stroke.path = new_path
            
            # Update width
            if prefix + "width" in params:
                new_stroke.width = params[prefix + "width"].item()
            
            # Update color
            if prefix + "color" in params:
                color = params[prefix + "color"].detach().cpu().numpy()
                new_stroke.color = tuple(color[:3].tolist())
            
            optimized.append(new_stroke)
        
        return optimized


class GradientDescentOptimizer:
    """
    Simple gradient descent optimizer without neural networks.
    
    Used when diffvg is not available, or for quick optimization.
    """
    
    def __init__(self, learning_rate: float = 0.1):
        """Initialize optimizer."""
        self.learning_rate = learning_rate
    
    def optimize(self, strokes: List[Stroke],
                 target_image: NDArray[np.uint8],
                 iterations: int = 50) -> List[Stroke]:
        """
        Simple gradient-free optimization.
        
        Uses local search with random perturbations.
        """
        # Convert target to grayscale for simpler comparison
        if len(target_image.shape) == 3:
            target_gray = np.mean(target_image, axis=2)
        else:
            target_gray = target_image
        
        # Simple perturbation-based optimization
        best_strokes = [s.clone() for s in strokes]
        best_error = self._compute_error(best_strokes, target_gray)
        
        for _ in range(iterations):
            # Perturb each stroke slightly
            new_strokes = []
            for stroke in strokes:
                new_stroke = stroke.clone()
                
                # Perturb width
                new_stroke.width *= np.random.uniform(0.95, 1.05)
                new_stroke.width = max(1.0, min(100.0, new_stroke.width))
                
                # Perturb color slightly
                new_color = []
                for c in stroke.color:
                    c += np.random.uniform(-0.05, 0.05)
                    new_color.append(max(0, min(1, c)))
                new_stroke.color = tuple(new_color)
                
                new_strokes.append(new_stroke)
            
            # Evaluate
            error = self._compute_error(new_strokes, target_gray)
            
            if error < best_error:
                best_error = error
                best_strokes = new_strokes
        
        return best_strokes
    
    def _compute_error(self, strokes: List[Stroke],
                       target: NDArray[np.float32]) -> float:
        """Compute rendering error vs target."""
        # Simple implementation: count strokes in regions
        # This is a placeholder for actual rendering
        
        h, w = target.shape
        error = 0.0
        
        for stroke in strokes:
            for x, y in stroke.path:
                ix = int(x) % w
                iy = int(y) % h
                # Penalize bright areas (dark strokes on bright = error)
                error += target[iy, ix] * stroke.color[0]
        
        return error / max(len(strokes), 1)
