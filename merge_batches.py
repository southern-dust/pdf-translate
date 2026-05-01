#!/usr/bin/env python3
"""Merge translated batch markdown files into a single draft."""

import argparse
import glob
import os
import re
import sys


def main():
    # -- Argument parsing ---------------------------------------------
    parser = argparse.ArgumentParser(
        description="Merge translated batch markdown files into a single draft"
    )
    parser.add_argument("--batches", required=True, help="Path to batches directory")
    parser.add_argument("--output", required=True, help="Output merged markdown file")
    args = parser.parse_args()

    # -- Validate input -----------------------------------------------
    if not os.path.isdir(args.batches):
        print(f"ERROR: batches directory not found: {args.batches}", file=sys.stderr)
        sys.exit(1)

    # -- Find batch files ---------------------------------------------
    pattern = os.path.join(args.batches, "batch_*_translated.md")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"ERROR: no batch_*_translated.md files found in {args.batches}", file=sys.stderr)
        sys.exit(1)

    # -- Merge --------------------------------------------------------
    with open(args.output, "w", encoding="utf-8") as out:
        for f in files:
            match = re.search(r"batch_(\d+)_", os.path.basename(f))
            batch_id = match.group(1) if match else "?"
            out.write(f"<!-- batch_{batch_id} start -->\n")
            with open(f, encoding="utf-8") as inf:
                out.write(inf.read().rstrip() + "\n")
            out.write(f"<!-- batch_{batch_id} end -->\n\n")

    print(f"Merged {len(files)} batch(es) → {args.output}")


if __name__ == "__main__":
    main()
