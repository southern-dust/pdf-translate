#!/usr/bin/env python3
"""Split extracted pages JSON into translation batches."""

import argparse
import json
import os
import sys

BATCH_SIZE_HELP = """
Batch size guidelines by page density:
  Dense tables/registers/diagrams  →  8-10  (e.g. PMIC datasheet)
  Moderate charts + text mix       →  12-15 (e.g. app note, whitepaper)
  Mostly prose, few figures        →  18-20 (e.g. software manual)
  Very sparse pages                →  25-30 (e.g. intro doc, TOC)

Default: 15
"""


def main():
    # -- Argument parsing -------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Split extracted pages JSON into translation batches",
        epilog=BATCH_SIZE_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Path to extracted_pages.json")
    parser.add_argument("--output", required=True, help="Output directory for batch files")
    parser.add_argument("--size", type=int, default=15, help="Pages per batch (default: 15)")
    args = parser.parse_args()

    # -- Validate arguments -----------------------------------------------
    if args.size < 1:
        print("ERROR: --size must be >= 1", file=sys.stderr)
        sys.exit(1)

    # -- Validate input ---------------------------------------------------
    if not os.path.exists(args.input):
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # -- Load pages -------------------------------------------------------
    with open(args.input, encoding="utf-8") as f:
        try:
            pages = json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: invalid JSON: {args.input}", file=sys.stderr)
            sys.exit(1)

    total_pages = len(pages)

    # -- Check for empty input --------------------------------------------
    if total_pages == 0:
        print("WARNING: No pages in input file")
        return

    if total_pages <= 5:
        print(f"Note: only {total_pages} pages — single batch, no parallelism needed")

    # -- Prepare output directory -----------------------------------------
    os.makedirs(args.output, exist_ok=True)

    # -- Write batch files ------------------------------------------------
    for i in range(0, total_pages, args.size):
        batch = pages[i:i + args.size]
        first, last = batch[0]["page"], batch[-1]["page"]
        batch_id = i // args.size + 1
        path = os.path.join(args.output, f"batch_{batch_id:02d}_p{first}-{last}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
        print(f"Batch {batch_id}: pages {first}-{last} → {path}")

    # -- Summary ----------------------------------------------------------
    batch_total = (total_pages + args.size - 1) // args.size
    print(f"\nTotal: {batch_total} batch(es) from {total_pages} pages")


if __name__ == "__main__":
    main()
