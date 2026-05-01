#!/usr/bin/env python3
"""Extract text and raster images from PDF pages to JSON."""

import argparse
import json
import os
import sys

try:
    import fitz
except ImportError:
    print("ERROR: PyMuPDF (fitz) is required. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # -- Argument parsing -------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Extract text and raster images from PDF pages to JSON"
    )
    parser.add_argument("--input", required=True, help="Path to input PDF")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    # -- Validate input ---------------------------------------------------
    if not os.path.exists(args.input):
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # -- Prepare output directories ---------------------------------------
    os.makedirs(args.output, exist_ok=True)
    img_dir = os.path.join(args.output, "images")
    os.makedirs(img_dir, exist_ok=True)

    # -- Extract pages ----------------------------------------------------
    doc = fitz.open(args.input)
    pages_data = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text(sort=True)
        image_list = page.get_images(full=True)
        page_images = []
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_filename = f"page{page_num+1:03d}_img{img_idx+1:02d}.{base_image['ext']}"
            with open(os.path.join(img_dir, img_filename), "wb") as f:
                f.write(base_image["image"])
            page_images.append(img_filename)
        pages_data.append({
            "page": page_num + 1,
            "text": text.strip(),
            "images": page_images,
        })

    doc.close()

    # -- Write output -----------------------------------------------------
    output_path = os.path.join(args.output, "extracted_pages.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pages_data, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(pages_data)} pages, {sum(len(p['images']) for p in pages_data)} images → {output_path}")


if __name__ == "__main__":
    main()
