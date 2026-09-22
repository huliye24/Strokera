"""SPP 0.1: a small, deterministic painting interchange format."""
from __future__ import annotations

import ast
import html
import json
import math
from pathlib import Path

VERSION = "spp/0.1"
FUNCS = {name: getattr(math, name) for name in ("sin", "cos", "tan", "sqrt", "log", "exp")}
CONSTS = {"pi": math.pi, "tau": math.tau, "e": math.e}


class ProtocolError(ValueError):
    pass


def number(value, label, low=-1e6, high=1e6):
    if type(value) not in (float, int) or not math.isfinite(value) or not low <= value <= high:
        raise ProtocolError(f"{label} must be a finite number in [{low}, {high}]")
    return float(value)


def color(value, label):
    if not isinstance(value, str) or len(value) != 7 or value[0] != "#" or any(c not in "0123456789abcdefABCDEF" for c in value[1:]):
        raise ProtocolError(f"{label} must be #RRGGBB")
    return value


def expression(source, t):
    if not isinstance(source, str) or len(source) > 160:
        raise ProtocolError("expression must be a string <= 160 chars")
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise ProtocolError("invalid expression") from exc

    def visit(node, depth=0):
        if depth > 20: raise ProtocolError("expression too deep")
        if isinstance(node, ast.Expression): return visit(node.body, depth+1)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float): return float(node.value)
        if isinstance(node, ast.Name) and node.id in {"t", *CONSTS}: return t if node.id == "t" else CONSTS[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = visit(node.operand, depth+1)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            a, b = visit(node.left, depth+1), visit(node.right, depth+1)
            if isinstance(node.op, ast.Add): return a+b
            if isinstance(node.op, ast.Sub): return a-b
            if isinstance(node.op, ast.Mult): return a*b
            if isinstance(node.op, ast.Div): return a/b
            if abs(b) > 8 or abs(a) > 1e6: raise ProtocolError("power limit exceeded")
            return a**b
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and len(node.args) == 1 and not node.keywords:
            return FUNCS[node.func.id](visit(node.args[0], depth+1))
        raise ProtocolError("unsupported expression syntax")

    try:
        return number(visit(tree), "expression result")
    except (ArithmeticError, OverflowError) as exc:
        raise ProtocolError("expression arithmetic error") from exc


def points(stroke):
    if "path" in stroke and "parametric" in stroke:
        raise ProtocolError("choose path or parametric, not both")
    if "path" in stroke:
        path = stroke["path"]
        if not isinstance(path, list) or not 2 <= len(path) <= 10000: raise ProtocolError("path needs 2..10000 points")
        result = []
        for point in path:
            if not isinstance(point, list) or len(point) != 2: raise ProtocolError("point must be [x,y]")
            result.append((number(point[0], "x"), number(point[1], "y")))
        return result
    curve = stroke.get("parametric")
    if not isinstance(curve, dict): raise ProtocolError("stroke needs path or parametric")
    steps = curve.get("steps", 128)
    if type(steps) is not int or not 2 <= steps <= 2000: raise ProtocolError("steps must be 2..2000")
    start, end = number(curve.get("from"), "from"), number(curve.get("to"), "to")
    if start >= end: raise ProtocolError("from must be less than to")
    return [(expression(curve.get("x"), start+(end-start)*i/(steps-1)), expression(curve.get("y"), start+(end-start)*i/(steps-1))) for i in range(steps)]


def validate(doc):
    if not isinstance(doc, dict) or doc.get("protocol") != VERSION: raise ProtocolError(f"protocol must be {VERSION}")
    canvas = doc.get("canvas")
    if not isinstance(canvas, dict): raise ProtocolError("canvas is required")
    for key in ("width", "height"): number(canvas.get(key), key, 1, 10000)
    color(canvas.get("background", "#FFFFFF"), "background")
    layers, strokes = doc.get("layers"), doc.get("strokes")
    if not isinstance(layers, list) or not 1 <= len(layers) <= 1000: raise ProtocolError("layers needs 1..1000 entries")
    if not isinstance(strokes, list) or len(strokes) > 100000: raise ProtocolError("strokes must be a list <= 100000")
    ids = set()
    for layer in layers:
        lid = layer.get("id") if isinstance(layer, dict) else None
        if not isinstance(lid, str) or not lid or lid in ids: raise ProtocolError("layer ids must be unique strings")
        ids.add(lid)
    stroke_ids = set()
    for stroke in strokes:
        sid = stroke.get("id") if isinstance(stroke, dict) else None
        if not isinstance(sid, str) or not sid or sid in stroke_ids: raise ProtocolError("stroke ids must be unique strings")
        stroke_ids.add(sid)
        if stroke.get("layer_id") not in ids: raise ProtocolError("unknown layer_id")
        number(stroke.get("width"), "width", .01, 1000)
        number(stroke.get("opacity", 1), "opacity", 0, 1)
        color(stroke.get("color"), "color")
        points(stroke)
    return doc


def load(path):
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def render_svg(doc):
    validate(doc)
    c = doc["canvas"]
    w, h = int(c["width"]), int(c["height"])
    result = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">', f'<rect width="100%" height="100%" fill="{c.get("background", "#FFFFFF")}"/>']
    for layer in doc["layers"]:
        result.append(f'<g data-layer="{html.escape(layer["id"], quote=True)}">')
        for stroke in doc["strokes"]:
            if stroke["layer_id"] != layer["id"]: continue
            coords = " ".join(f"{x:.3f},{y:.3f}" for x, y in points(stroke))
            result.append(f'<polyline data-stroke="{html.escape(stroke["id"], quote=True)}" points="{coords}" fill="none" stroke="{stroke["color"]}" stroke-width="{stroke["width"]}" stroke-opacity="{stroke.get("opacity", 1)}" stroke-linecap="round" stroke-linejoin="round"/>')
        result.append("</g>")
    return "\n".join(result + ["</svg>"])
