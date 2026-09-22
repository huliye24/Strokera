<p align="center"><img src="brand/assets/github-header.png" alt="Strokera — The Painting Process Protocol" width="100%"></p>

# Strokera

[品牌横图与 UI 配图](brand/README.md) · [视觉展示页](brand/showcase.html)

**A painting protocol, not a one-click image generator.**

Strokera takes inspiration from the creative control of function drawing: an artist or agent can specify curves, then build a painting through ordered layers and visible, editable strokes. The source of truth is a painting plan, not a flattened picture. A screen preview lets a person watch the construction and intervene; the protocol and CLI remain the core.

## Project status

**Initiation / SPP 0.1 draft.** The working standard-library CLI validates an SPP document, renders SVG, and generates a self-contained playback page. Existing `src/strokera/core`, `planning`, and `optimize` modules are earlier experimental research code, not yet wired into the new protocol CLI. Physical brush simulation, reference-image analysis, GUI editing, and agent planning are future work, not current claims.

## Quick start

```bash
python -m pip install -e .
strokera validate examples/river-study.json
strokera render examples/river-study.json -o river.svg
strokera preview examples/river-study.json -o river.html
```

Successful CLI calls emit one JSON object to stdout; failures emit one JSON object to stderr and exit with code 2. This makes tool calling predictable for agents. `preview` produces a local HTML screen with a stroke-sequence slider and playback control.

## Model

```text
painting document (SPP)
  canvas → layers (back to front) → strokes (ordered within each layer)
                                  ↳ sampled path or safe parametric x(t), y(t)
                ↓
             CLI validate / render / preview
                ↓
             artist review, edit, iterate
```

SPP preserves deliberate construction: layers, stroke order, width, color and opacity. Parametric curves are sampled deterministically with a restricted mathematical grammar; the CLI does not execute arbitrary Python. The format is defined in [SPP 0.1](docs/SPP-0.1.md), with a runnable [example](examples/river-study.json). The [project charter](docs/PROJECT.md) states scope, milestones, and acceptance criteria.

## Principles

- Artist control before automation. AI suggests or drafts strokes; the author can inspect and change them.
- Process is first-class. Playback and layered structure matter as much as the final SVG.
- Visual depth comes from composition, occlusion, order, brush intent and revision, not just more pixels.
- Protocol first. The screen is a view of a portable document, not a proprietary source format.
- Equation curves alone are not painting: expressive brush dynamics and material behavior need later versions.

## Repository

`src/strokera/protocol.py` defines validation and SVG rendering; `protocol_cli.py` exposes agent commands; `examples/` contains a human-editable sample; `docs/` holds protocol and planning material. Earlier prototype modules are retained for research and will be integrated only after their APIs and tests are repaired.

## License

GPL-3.0-only, matching the GitHub repository's existing license. Third-party model or rendering code must be reviewed before integration; linked research projects are references, not bundled dependencies.
