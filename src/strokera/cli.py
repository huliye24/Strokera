"""
Strokera CLI - Command-line interface for stroke-based painting.

Usage:
    strokera paint input.png --strokes 1000
    strokera analyze input.png
    strokera render portrait.stroke --output result.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, List, Tuple

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table

from strokera import __version__
from strokera.core import Canvas, Brush, BrushEngine, StrokeGraph
from strokera.planning import ImageAnalyzer, PaintingPlanner, StrokePlanner
from strokera.optimize import GradientDescentOptimizer
from strokera.io import StrokeFile

console = Console()


@click.group()
@click.version_option(version=__version__)
def main():
    """Strokera - Open Painting Runtime"""
    pass


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--strokes", "-s", default=1000, help="Number of strokes to generate")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--brush", "-b", default="oil_round", help="Brush preset")
@click.option("--strategy", default="auto", help="Painting strategy (auto/portrait/landscape)")
@click.option("--width", "-w", type=int, default=1024, help="Output width")
@click.option("--height", "-h", type=int, default=1024, help="Output height")
@click.option("--save-stroke", type=click.Path(), help="Save .stroke file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def paint(input, strokes, output, brush, strategy, width, height, save_stroke, verbose):
    """Paint an image using stroke-based rendering."""
    
    console.print(f"[bold blue]Strokera v{__version__}[/bold blue]")
    console.print(f"[dim]Input:[/dim] {input}")
    console.print(f"[dim]Target strokes:[/dim] {strokes}")
    console.print()
    
    try:
        # Load image
        from PIL import Image
        import numpy as np
        
        img = Image.open(input)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img_array = np.array(img)
        
        # Step 1: Analyze image
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            
            # Analyze
            task = progress.add_task("[cyan]Analyzing image...", total=100)
            analyzer = ImageAnalyzer()
            analysis = analyzer.analyze(img_array, mode=ImageAnalyzer.AnalysisMode.STANDARD)
            progress.update(task, advance=30)
            
            # Plan
            progress.update(task, description="[cyan]Planning painting...")
            planner = PaintingPlanner()
            plan = planner.plan(analysis, strategy=strategy, target_strokes=strokes)
            progress.update(task, advance=30)
            
            # Generate strokes
            progress.update(task, description="[cyan]Generating strokes...")
            brush_obj = Brush.create_preset(brush)
            stroke_planner = StrokePlanner()
            
            stroke_graph = stroke_planner.plan(
                plan, 
                brush=brush_obj,
                progress_callback=lambda i, t, s: progress.update(
                    task, 
                    advance=20 * (1 if i == t else 0.1),
                    description=f"[cyan]Generating strokes... {i}/{t}"
                )
            )
            progress.update(task, advance=20)
            
            # Render
            progress.update(task, description="[cyan]Rendering canvas...")
            canvas = Canvas(width, height, background=(255, 255, 255))
            brush_engine = BrushEngine((width, height))
            brush_engine.render_stroke_graph(stroke_graph, brush_obj, canvas.layers[list(canvas.layers.keys())[0]].pixels[:, :, :3])
            progress.update(task, advance=10)
            
            # Finalize
            progress.update(task, description="[cyan]Finalizing...", completed=100)
        
        # Save outputs
        if save_stroke:
            console.print(f"\n[dim]Saving stroke file:[/dim] {save_stroke}")
            stroke_file = StrokeFile()
            stroke_file.save(save_stroke, stroke_graph, canvas)
        
        if output:
            console.print(f"\n[dim]Saving image:[/dim] {output}")
            result = canvas.render()
            result_img = Image.fromarray(result)
            result_img.save(output)
        
        # Stats
        console.print()
        table = Table(title="Painting Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        stats = stroke_graph.get_stats()
        table.add_row("Total Strokes", str(stats["total_strokes"]))
        table.add_row("Layers", str(stats["total_layers"]))
        table.add_row("Groups", str(stats["total_groups"]))
        table.add_row("Processing Time", f"{progress._tasks[0].finished_time:.2f}s")
        
        console.print(table)
        console.print(f"\n[bold green]✓[/bold green] Painting complete!")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def analyze(input, output, verbose):
    """Analyze an image and show its structure."""
    
    console.print(f"[bold blue]Analyzing:[/bold blue] {input}")
    
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.open(input)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img_array = np.array(img)
        
        analyzer = ImageAnalyzer()
        result = analyzer.analyze(img_array, mode=ImageAnalyzer.AnalysisMode.FULL)
        
        # Display results
        console.print()
        console.print(Panel.fit(
            f"[bold]Image Analysis Results[/bold]\n\n"
            f"Size: {result.width} × {result.height}\n"
            f"Segments: {len(result.segments)}\n"
            f"Edge Strength: {result.edge_strength:.3f}\n"
            f"Processing Time: {result.processing_time:.2f}s"
        ))
        
        # Show segments
        if result.segments:
            console.print()
            table = Table(title="Detected Regions")
            table.add_column("Label", style="cyan")
            table.add_column("Area", style="yellow")
            table.add_column("Importance", style="green")
            
            sorted_segs = result.get_segments_sorted("importance")[:10]
            for seg in sorted_segs:
                table.add_row(
                    seg.label,
                    f"{seg.area:.0f}",
                    f"{seg.importance:.2f}"
                )
            
            console.print(table)
        
        # Save JSON if requested
        if output:
            with open(output, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            console.print(f"\n[dim]Analysis saved to:[/dim] {output}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("stroke_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output image file")
@click.option("--format", "-f", type=click.Choice(["png", "jpg", "svg"]), default="png", help="Output format")
def render(stroke_file, output, format):
    """Render a .stroke file to an image."""
    
    console.print(f"[bold blue]Rendering:[/bold blue] {stroke_file}")
    
    try:
        stroke_file_obj = StrokeFile()
        graph, canvas_data = stroke_file_obj.load(stroke_file)
        
        # Reconstruct canvas
        canvas = Canvas.from_dict(canvas_data)
        
        # Render
        brush = Brush.create_preset("oil_round")
        engine = BrushEngine((canvas.width, canvas.height))
        
        layer_id = list(canvas.layers.keys())[0]
        engine.render_stroke_graph(graph, brush, canvas.layers[layer_id].pixels[:, :, :3])
        
        # Save
        if output:
            from PIL import Image
            result = canvas.render()
            result_img = Image.fromarray(result)
            result_img.save(output)
            console.print(f"[green]✓[/green] Saved to {output}")
        else:
            console.print(f"[dim]Rendered {len(graph.strokes)} strokes[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("stroke_file", type=click.Path(exists=True))
def info(stroke_file):
    """Show information about a .stroke file."""
    
    try:
        stroke_file_obj = StrokeFile()
        graph, canvas_data = stroke_file_obj.load(stroke_file)
        
        stats = graph.get_stats()
        
        console.print(Panel.fit(
            f"[bold].stroke File Info[/bold]\n\n"
            f"File: {stroke_file}\n"
            f"Total Strokes: {stats['total_strokes']}\n"
            f"Layers: {stats['total_layers']}\n"
            f"Groups: {stats['total_groups']}\n"
            f"Graph ID: {graph.id}"
        ))
        
        # Layer breakdown
        if stats["layers"]:
            table = Table(title="Layers")
            table.add_column("Layer", style="cyan")
            table.add_column("Strokes", style="yellow")
            table.add_column("Length", style="green")
            
            for layer_id, layer_stats in stats["layers"].items():
                table.add_row(
                    layer_id,
                    str(layer_stats["count"]),
                    f"{layer_stats['total_length']:.0f}"
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@main.command()
def list_brushes():
    """List available brush presets."""
    
    brushes = [
        ("oil_round", "Round oil brush"),
        ("oil_flat", "Flat oil brush"),
        ("watercolor", "Watercolor brush"),
        ("marker", "Marker pen"),
        ("ink_brush", "Ink brush"),
        ("pencil", "Pencil"),
        ("charcoal", "Charcoal"),
    ]
    
    table = Table(title="Available Brushes")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="yellow")
    
    for name, desc in brushes:
        table.add_row(name, desc)
    
    console.print(table)


if __name__ == "__main__":
    main()
