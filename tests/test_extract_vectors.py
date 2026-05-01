import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import extract_vectors as ev


def test_area():
    """_area returns width * height."""
    class Rect:
        pass
    r = Rect()
    r.x0, r.y0, r.x1, r.y1 = 0, 0, 10, 20
    assert ev._area(r) == 200


def test_merge_rects_no_overlap():
    """Non-overlapping rects stay separate."""
    try:
        import fitz
    except ImportError:
        return
    a = fitz.Rect(0, 0, 10, 10)
    b = fitz.Rect(20, 20, 30, 30)
    result = ev.merge_rects([a, b], gap=5)
    assert len(result) == 2


def test_merge_rects_overlap():
    """Overlapping rects merge."""
    try:
        import fitz
    except ImportError:
        return
    a = fitz.Rect(0, 0, 10, 10)
    b = fitz.Rect(5, 5, 15, 15)
    result = ev.merge_rects([a, b], gap=5)
    assert len(result) == 1


def test_merge_rects_gap_merges():
    """Rects within gap merge."""
    try:
        import fitz
    except ImportError:
        return
    a = fitz.Rect(0, 0, 10, 10)
    b = fitz.Rect(15, 0, 25, 10)
    result = ev.merge_rects([a, b], gap=10)
    assert len(result) == 1


def test_merge_rects_beyond_gap():
    """Rects beyond gap stay separate."""
    try:
        import fitz
    except ImportError:
        return
    a = fitz.Rect(0, 0, 10, 10)
    b = fitz.Rect(21, 0, 31, 10)
    result = ev.merge_rects([a, b], gap=10)
    assert len(result) == 2


def test_merge_rects_empty():
    """Empty list returns empty."""
    assert ev.merge_rects([]) == []


def test_clip_svg_with_namespace():
    """clip_svg handles SVG with XML namespace correctly."""
    import tempfile
    import xml.etree.ElementTree as ET

    try:
        import fitz
    except ImportError:
        return

    SVG_NS = "http://www.w3.org/2000/svg"
    svg_content = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="{SVG_NS}" width="100" height="100">'
        f'<rect width="100" height="100"/></svg>'
    )

    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as tmp:
        tmp.write(svg_content)
        full_svg = tmp.name

    try:
        output_svg = full_svg.replace(".svg", "_clipped.svg")
        rect = fitz.Rect(10, 10, 50, 50)
        ev.clip_svg(full_svg, rect, output_svg)

        assert os.path.exists(output_svg)
        result_tree = ET.parse(output_svg)
        result_root = result_tree.getroot()
        assert "viewBox" in result_root.attrib
    finally:
        os.unlink(full_svg)
        if os.path.exists(output_svg):
            os.unlink(output_svg)


def test_clip_svg_no_namespace():
    """clip_svg handles SVG without namespace prefix."""
    import tempfile
    import xml.etree.ElementTree as ET

    try:
        import fitz
    except ImportError:
        return

    SVG_NS = "http://www.w3.org/2000/svg"
    svg_content = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="{SVG_NS}" width="100" height="100">'
        f'<rect width="100" height="100"/></svg>'
    )

    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as tmp:
        tmp.write(svg_content)
        full_svg = tmp.name

    try:
        output_svg = full_svg.replace(".svg", "_clipped.svg")
        rect = fitz.Rect(0, 0, 100, 100)
        ev.clip_svg(full_svg, rect, output_svg)

        assert os.path.exists(output_svg)
        result_tree = ET.parse(output_svg)
        result_root = result_tree.getroot()
        assert "viewBox" in result_root.attrib
    finally:
        os.unlink(full_svg)
        if os.path.exists(output_svg):
            os.unlink(output_svg)
