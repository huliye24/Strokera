"""Agent-facing protocol CLI. Stdout is always one JSON object."""
import argparse
import html
import json
import sys
from pathlib import Path

from .protocol import load, render_svg


def main(argv=None):
    parser = argparse.ArgumentParser(prog="strokera", description="Strokera Painting Protocol 0.1")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "render", "preview"):
        cmd = sub.add_parser(name)
        cmd.add_argument("input", type=Path)
        if name != "validate": cmd.add_argument("--output", "-o", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        doc = load(args.input)
        if args.command == "validate":
            result = {"ok": True, "protocol": doc["protocol"], "layers": len(doc["layers"]), "strokes": len(doc["strokes"])}
        elif args.command == "render":
            if args.output.suffix.lower() != ".svg": raise ValueError("render output must be .svg")
            args.output.write_text(render_svg(doc), encoding="utf-8")
            result = {"ok": True, "output": str(args.output), "format": "svg"}
        else:
            if args.output.suffix.lower() != ".html": raise ValueError("preview output must be .html")
            svg = render_svg(doc)
            title = html.escape(str(doc.get("title", "Strokera preview")))
            page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>body{{margin:0;background:#121719;color:#eee6da;font:15px system-ui;display:grid;grid-template-columns:minmax(0,1fr) 280px;min-height:100vh}}main{{display:grid;place-items:center;padding:24px}}svg{{max-width:100%;max-height:85vh;box-shadow:0 22px 60px #0009}}aside{{padding:28px;background:#20292b}}input{{width:100%}}small{{color:#c6bda9}}button{{padding:8px 16px}}@media(max-width:700px){{body{{display:block}}}}</style>
<main>{svg}</main><aside><h1>Strokera</h1><p>{title}</p><small>Layered stroke process · spp/0.1</small><p><input id="step" type="range" min="0" max="{len(doc['strokes'])}" value="{len(doc['strokes'])}"></p><output id="count"></output><p><button id="play">Play</button></p><small>Preview only. Edit the source .json to change strokes.</small></aside>
<script>const s=[...document.querySelectorAll('[data-stroke]')],i=document.querySelector('#step'),o=document.querySelector('#count');function draw(){{let n=+i.value;s.forEach((e,j)=>e.style.visibility=j<n?'visible':'hidden');o.value=n+' / '+s.length+' strokes'}}i.oninput=draw;document.querySelector('#play').onclick=()=>{{i.value=0;draw();let timer=setInterval(()=>{{i.value=Math.min(+i.value+1,s.length);draw();if(+i.value===s.length)clearInterval(timer)}},150)}};draw()</script></html>'''
            args.output.write_text(page, encoding="utf-8")
            result = {"ok": True, "output": str(args.output), "format": "html"}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
