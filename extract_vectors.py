#!/usr/bin/env python3
"""
Extract vector graphics from PDF pages as SVG + PNG fallback.

Approach:
  1. Detect vector graphics regions via page.get_drawings()
  2. Mask text (white rectangles) to isolate vector graphics
  3. Convert masked page to SVG via pdftocairo
  4. Clip each region as a standalone SVG (viewBox windowing)
  5. Render each region as high-DPI PNG fallback

Output:
  vectors/page_NNN_vMM.svg  — clipped vector graphic
  vectors/page_NNN_vMM.png  — 300 DPI raster fallback
  vectors/manifest.json     — page → region → file mapping
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from copy import deepcopy

try:
    import fitz
except ImportError:
    print("ERROR: PyMuPDF (fitz) is required. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

SVG_NS = "http://www.w3.org/2000/svg"


# ---------------------------------------------------------------------------
# Rectangle utilities
# ---------------------------------------------------------------------------

def _area(r):
    return (r.x1 - r.x0) * (r.y1 - r.y0)


def merge_rects(rects, gap=10):
    """
    Merge overlapping or nearby rectangles.
    Sorts by area (largest first), then greedily merges rects within `gap` points.
    """
    if not rects:
        return []
    sorted_rects = sorted(rects, key=_area, reverse=True)
    groups = []
    for rect in sorted_rects:
        fitted = False
        for i, group in enumerate(groups):
            expanded = fitz.Rect(
                group.x0 - gap, group.y0 - gap,
                group.x1 + gap, group.y1 + gap,
            )
            if expanded.intersects(rect):
                groups[i] = group | rect
                fitted = True
                break
        if not fitted:
            groups.append(fitz.Rect(rect))
    return groups


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def get_vector_regions(page, min_area=5000):
    """
    Return merged bounding boxes for vector graphics on a page.
    Uses page.get_drawings() and filters by minimum area (pt²).
    """
    drawings = page.get_drawings()
    rects = []
    for d in drawings:
        r = fitz.Rect(d["rect"])
        if _area(r) >= min_area:
            rects.append(r)
    return merge_rects(rects)


def mask_text_on_page(page):
    """Draw white filled rectangles over every text block on a page."""
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:  # text
            bbox = fitz.Rect(block["bbox"])
            page.draw_rect(bbox, color=(1, 1, 1), fill=(1, 1, 1))


def make_masked_single_page_pdf(doc, page_num, dst_path):
    """
    Create a single-page PDF from `doc[page_num]` with text masked,
    saved to `dst_path`.
    """
    single = fitz.open()
    single.insert_pdf(doc, from_page=page_num, to_page=page_num)
    sp = single[0]
    mask_text_on_page(sp)
    single.save(dst_path)
    single.close()


# ---------------------------------------------------------------------------
# SVG clipping
# ---------------------------------------------------------------------------

def clip_svg(full_svg_path, rect, output_path):
    """
    Create a clipped SVG by setting viewBox to `rect`.
    All elements are deep-copied from the full-page SVG; the viewBox
    acts as a window — elements outside the region are not visible.
    Detects namespace from root element to handle pdftocairo variations.
    """
    ET.register_namespace("", SVG_NS)
    tree = ET.parse(full_svg_path)
    root = tree.getroot()

    actual_tag = root.tag
    if actual_tag.startswith("{"):
        actual_ns = actual_tag.split("}")[0] + "}"
    else:
        actual_ns = ""

    w = rect.x1 - rect.x0
    h = rect.y1 - rect.y0

    tag = f"{actual_ns}svg" if actual_ns else "svg"
    new_root = ET.Element(tag)
    new_root.set("viewBox", f"{rect.x0} {rect.y0} {w} {h}")
    new_root.set("width", f"{w}")
    new_root.set("height", f"{h}")

    for child in root:
        new_root.append(deepcopy(child))

    new_tree = ET.ElementTree(new_root)
    new_tree.write(output_path, encoding="utf-8", xml_declaration=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract vector graphics from PDF pages (SVG + PNG fallback)"
    )
    parser.add_argument("--input", required=True, help="Path to input PDF")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--pages",
        help="Pages to process: comma-separated and/or ranges, e.g. '1-10' or '5,8,12'",
    )
    parser.add_argument("--dpi", type=int, default=300, help="PNG fallback DPI (default: 300)")
    parser.add_argument(
        "--min-area", type=int, default=5000,
        help="Minimum vector region area in pt² (default: 5000)",
    )
    parser.add_argument(
        "--gap", type=int, default=10,
        help="Max gap in points for merging adjacent regions (default: 10)",
    )
    args = parser.parse_args()

    # -- Check dependencies -----------------------------------------------
    if not shutil.which("pdftocairo"):
        print("ERROR: pdftocairo not found. Install poppler-utils:", file=sys.stderr)
        print("  apt install poppler-utils")
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    output_parent = os.path.dirname(os.path.abspath(args.output))
    if not os.path.isdir(output_parent):
        print(f"ERROR: output parent directory not found: {output_parent}")
        sys.exit(1)

    doc = fitz.open(args.input)
    total_pages = doc.page_count

    # -- Parse page range ----------------------------------------------------
    if args.pages:
        pages_to_process = set()
        for part in args.pages.split(","):
            part = part.strip()
            if "-" in part:
                start_str, end_str = part.split("-", 1)
                start = int(start_str) - 1
                end = min(int(end_str), total_pages)
                pages_to_process.update(range(max(start, 0), end))
            else:
                p = int(part) - 1
                if 0 <= p < total_pages:
                    pages_to_process.add(p)
    else:
        pages_to_process = set(range(total_pages))

    # -- Output dirs ---------------------------------------------------------
    svg_dir = os.path.join(args.output, "vectors")
    os.makedirs(svg_dir, exist_ok=True)

    manifest = OrderedDict()
    total_extracted = 0

    for page_num in sorted(pages_to_process):
        page_label = page_num + 1
        page = doc[page_num]

        print(f"--- Page {page_label}/{total_pages} ---")

        # 1. Detect vector regions
        regions = get_vector_regions(page, args.min_area)
        if not regions:
            print("  No vector graphics (above min-area threshold)")
            manifest[f"page_{page_label:03d}"] = {"page": page_label, "vectors": []}
            continue

        print(f"  {len(regions)} region(s) detected")

        # 2. Build masked single-page PDF → convert to SVG
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_pdf = tmp.name
        try:
            make_masked_single_page_pdf(doc, page_num, tmp_pdf)

            svg_base = os.path.join(svg_dir, f"_tmp_page_{page_label:03d}")
            full_svg_path = svg_base + ".svg"
            result = subprocess.run(
                ["pdftocairo", "-svg", "-f", "1", "-l", "1", tmp_pdf, full_svg_path],
                capture_output=True, text=True,
            )
            # pdftocairo writes to the exact path given; font warnings on
            # stderr are harmless as long as the SVG file was produced
            if not os.path.exists(full_svg_path):
                print(f"  WARNING: pdftocairo did not produce SVG output")
                if result.stderr.strip():
                    fontless = [l for l in result.stderr.splitlines()
                                if "font" not in l.lower()]
                    if fontless:
                        print(f"  stderr: {fontless[0][:200]}")
                manifest[f"page_{page_label:03d}"] = {"page": page_label, "vectors": []}
                continue
        finally:
            os.unlink(tmp_pdf)

        # 3. Clip each region → SVG + PNG
        page_vectors = []
        for i, rect in enumerate(regions):
            vec_id = f"v{i+1:02d}"
            status = []

            clipped_svg = os.path.join(svg_dir, f"page_{page_label:03d}_{vec_id}.svg")
            try:
                clip_svg(full_svg_path, rect, clipped_svg)
                status.append("svg")
            except Exception as exc:
                print(f"  WARNING: SVG clip failed for {vec_id}: {exc}")
                clipped_svg = None

            png_path = os.path.join(svg_dir, f"page_{page_label:03d}_{vec_id}.png")
            try:
                pix = page.get_pixmap(dpi=args.dpi, clip=rect)
                pix.save(png_path)
                status.append("png")
            except Exception as exc:
                print(f"  WARNING: PNG render failed for {vec_id}: {exc}")
                png_path = None

            entry = {
                "id": vec_id,
                "bbox": [round(rect.x0, 1), round(rect.y0, 1),
                         round(rect.x1, 1), round(rect.y1, 1)],
                "svg": os.path.relpath(clipped_svg, args.output) if clipped_svg else None,
                "png": os.path.relpath(png_path, args.output) if png_path else None,
            }
            page_vectors.append(entry)
            print(f"  {vec_id}: bbox={rect}  [{', '.join(status)}]")
            total_extracted += 1

        # Clean up full-page SVG
        os.unlink(full_svg_path)

        manifest[f"page_{page_label:03d}"] = {"page": page_label, "vectors": page_vectors}

    doc.close()

    # 4. Write manifest
    manifest_path = os.path.join(svg_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {total_extracted} vector graphic(s) → {svg_dir}/")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
