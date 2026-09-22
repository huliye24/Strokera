import copy
import json
from pathlib import Path

import pytest

from strokera.protocol import ProtocolError, load, render_svg, validate
from strokera.protocol_cli import main


SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "river-study.json"


def test_sample_renders_deterministically():
    doc = load(SAMPLE)
    first = render_svg(doc)
    assert first == render_svg(doc)
    assert first.count("<polyline") == 5
    assert "data-layer=\"current\"" in first


def test_rejects_python_execution():
    doc = copy.deepcopy(load(SAMPLE))
    doc["strokes"][1]["parametric"]["x"] = "__import__('os').system('whoami')"
    with pytest.raises(ProtocolError):
        validate(doc)


def test_rejects_unknown_layer_and_duplicate_id():
    doc = copy.deepcopy(load(SAMPLE))
    doc["strokes"][0]["layer_id"] = "missing"
    with pytest.raises(ProtocolError): validate(doc)
    doc = copy.deepcopy(load(SAMPLE))
    doc["strokes"][1]["id"] = doc["strokes"][0]["id"]
    with pytest.raises(ProtocolError): validate(doc)


def test_cli_outputs(tmp_path, capsys):
    svg, page = tmp_path / "out.svg", tmp_path / "out.html"
    assert main(["validate", str(SAMPLE)]) == 0
    assert json.loads(capsys.readouterr().out)["ok"]
    assert main(["render", str(SAMPLE), "-o", str(svg)]) == 0
    assert "<svg" in svg.read_text(encoding="utf-8")
    assert main(["preview", str(SAMPLE), "-o", str(page)]) == 0
    assert "Play" in page.read_text(encoding="utf-8")
