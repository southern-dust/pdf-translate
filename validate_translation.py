#!/usr/bin/env python3
"""Mechanical validation of translated markdown before proofreading.

Checks (deterministic only):
  1. All image references point to existing files
  2. Batch marker count matches source batch file count
  3. (Optional) Glossary term string presence in draft

Outputs PASS/FAIL with structured issues list.
"""

import argparse
import os
import re
import sys


def check_images(draft_path, images_dir):
    """Check all ![xxx](...) references (images/ and vectors/) point to existing files."""
    vectors_dir = os.path.join(os.path.dirname(images_dir), "vectors")
    issues = []
    pattern = re.compile(r'!\[.*?\]\(((?:images|vectors)/[^)]+)\)')
    with open(draft_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            for match in pattern.finditer(line):
                rel_path = match.group(1)
                if rel_path.startswith("images/"):
                    filename = rel_path[len("images/"):]
                    base_dir = images_dir
                else:
                    filename = rel_path[len("vectors/"):]
                    base_dir = vectors_dir
                abs_path = os.path.normpath(os.path.join(base_dir, filename))
                if not os.path.exists(abs_path):
                    issues.append(
                        f"Line {lineno}: MISSING_IMAGE {rel_path}"
                    )
    return issues


def check_batch_count(draft_path, batches_dir):
    """Verify batch marker count matches number of source batch files."""
    issues = []
    source_batches = sorted(
        f for f in os.listdir(batches_dir)
        if re.match(r'batch_\d+_translated\.md$', f)
    )
    source_ids = set()
    for f in source_batches:
        m = re.search(r'batch_(\d+)_', f)
        if m:
            source_ids.add(int(m.group(1)))

    draft_ids = set()
    with open(draft_path, encoding="utf-8") as f:
        for line in f:
            m = re.search(r'<!-- batch_(\d+) start -->', line)
            if m:
                draft_ids.add(int(m.group(1)))

    missing = source_ids - draft_ids
    extra = draft_ids - source_ids
    for bid in sorted(missing):
        issues.append(f"BATCH_COUNT: batch {bid:02d} in source but missing in draft")
    for bid in sorted(extra):
        issues.append(f"BATCH_COUNT: batch {bid:02d} in draft but missing in source")
    return issues


def check_glossary_terms(draft_path, glossary_path):
    """Check glossary terms appear in draft (string match, no semantics)."""
    if not glossary_path or not os.path.exists(glossary_path):
        if glossary_path:
            print(f"WARNING: glossary file not found, skipping: {glossary_path}", file=sys.stderr)
        return []

    issues = []
    with open(glossary_path, encoding="utf-8") as f:
        glossary = f.read()

    terms = []
    for line in glossary.splitlines():
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if len(cols) >= 2:
            term = cols[0].strip()
            if term.startswith("-"):
                continue
            if term and term not in ("English Term", "---", "Source Term"):
                terms.append(term)

    with open(draft_path, encoding="utf-8") as f:
        draft = f.read()

    for term in terms:
        if term not in draft:
            issues.append(f"GLOSSARY: term '{term}' not found in draft")
    return issues


def main():
    # -- Argument parsing ---------------------------------------------
    parser = argparse.ArgumentParser(
        description="Mechanical validation of translated markdown (before proofread)"
    )
    parser.add_argument("--draft", required=True, help="Path to merged draft markdown")
    parser.add_argument("--batches", required=True, help="Path to batches directory")
    parser.add_argument("--images", required=True, help="Path to images directory")
    parser.add_argument("--glossary", default=None, help="Optional path to glossary.md")
    args = parser.parse_args()

    # -- Validate input -----------------------------------------------
    if not os.path.exists(args.draft):
        print(f"ERROR: draft file not found: {args.draft}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.batches):
        print(f"ERROR: batches directory not found: {args.batches}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.images):
        print(f"ERROR: images directory not found: {args.images}", file=sys.stderr)
        sys.exit(1)

    # -- Run checks ---------------------------------------------------
    all_issues = []

    issues = check_images(args.draft, args.images)
    all_issues.extend(issues)
    print(f"Image references: {'PASS' if not issues else 'FAIL'} ({len(issues)} issue(s))")

    issues = check_batch_count(args.draft, args.batches)
    all_issues.extend(issues)
    print(f"Batch count:      {'PASS' if not issues else 'FAIL'} ({len(issues)} issue(s))")

    if args.glossary:
        issues = check_glossary_terms(args.draft, args.glossary)
        all_issues.extend(issues)
        print(f"Glossary terms:   {'PASS' if not issues else 'FAIL'} ({len(issues)} issue(s))")

    if all_issues:
        print(f"\n--- ISSUES ({len(all_issues)}) ---", file=sys.stderr)
        for issue in all_issues:
            print(f"  {issue}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nAll checks passed.")


if __name__ == "__main__":
    main()
