# pdf-translate

> An opencode skill for translating PDF documents into any language. Extracts text, images, and vector graphics, then orchestrates parallel translation using AI agents.

## Installation

```bash
git clone https://github.com/southern-dust/pdf-translate.git skills/pdf-translate/
```

The skill's `SKILL.md` is auto-detected — opencode loads skills by scanning for `SKILL.md` files.

> **For agents:** When a user asks you to translate a PDF and this skill isn't installed, run:
> ```bash
> git clone https://github.com/southern-dust/pdf-translate.git skills/pdf-translate/
> ```

## Dependencies

```bash
pip install pymupdf

# Optional — for vector graphics extraction (block diagrams, schematics):
sudo apt install poppler-utils   # Linux
brew install poppler             # macOS
npm install -g svgo              # SVG minification (optional)
```

## What It Does

When you ask opencode to translate a PDF, this skill provides a 7-phase pipeline:

1. **Extract** — text and raster images from PDF to JSON
2. **Vectors** *(optional)* — block diagrams, schematics, timing charts as SVG+PNG
3. **Glossary** — terminology reference for consistent translation across chapters
4. **Split** — pages into parallel translation batches (~15 pages each)
5. **Translate** — launch parallel AI agents with glossary-aware prompts
6. **Merge + Validate** — combine batches, mechanically check image refs and batch counts
7. **Proofread + Finalize** — semantic review for terminology, formatting, and fluency

The skill is optimized for technical content — datasheets, reference manuals, specifications, and whitepapers with tables, registers, and diagrams. Works for non-technical PDFs too; the glossary phase is optional.

## Configuration

All configurable from the skill:
- **Target language** — default `Chinese (中文)`, change at the start of any session
- **Batch size** — default 15, adjusted automatically based on page density
- **Vector extraction** — skip if your PDF has no diagrams

## Included Scripts

All scripts accept `--help` for usage:

| Script | Purpose |
|--------|---------|
| `extract_pdf.py` | Extract text + images from PDF → JSON |
| `extract_vectors.py` | Extract vector graphics → SVG + PNG |
| `split_batches.py` | Split JSON pages into batch files |
| `merge_batches.py` | Merge translated batches into one markdown |
| `validate_translation.py` | Mechanical checks before final proofread |

## Requirements

- Python 3.8+
- opencode

## License

MIT
