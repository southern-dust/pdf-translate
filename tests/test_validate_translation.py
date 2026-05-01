import os
import subprocess
import sys
import tempfile


def make_draft(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_validate_all_images_exist():
    """All image references point to existing files → PASS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = os.path.join(tmpdir, "images")
        os.makedirs(images_dir)
        open(os.path.join(images_dir, "fig1.png"), "w").close()
        open(os.path.join(images_dir, "fig2.png"), "w").close()

        draft = os.path.join(tmpdir, "draft.md")
        make_draft(draft, "Some text\n![Fig 1](images/fig1.png)\n![Fig 2](images/fig2.png)\n")

        batches_dir = os.path.join(tmpdir, "batches")
        os.makedirs(batches_dir)

        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/validate_translation.py",
             "--draft", draft, "--batches", batches_dir, "--images", images_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "PASS" in result.stdout


def test_validate_missing_image():
    """Image referenced but file missing → FAIL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = os.path.join(tmpdir, "images")
        os.makedirs(images_dir)

        draft = os.path.join(tmpdir, "draft.md")
        make_draft(draft, "![Missing](images/nonexistent.png)\n")

        batches_dir = os.path.join(tmpdir, "batches")
        os.makedirs(batches_dir)

        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/validate_translation.py",
             "--draft", draft, "--batches", batches_dir, "--images", images_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "MISSING_IMAGE" in result.stderr


def test_validate_batch_count():
    """Batch markers in draft mismatch batch files → FAIL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = os.path.join(tmpdir, "images")
        os.makedirs(images_dir)

        batches_dir = os.path.join(tmpdir, "batches")
        os.makedirs(batches_dir)
        for i in [1, 2]:
            p = os.path.join(batches_dir, f"batch_{i:02d}_translated.md")
            with open(p, "w") as f:
                f.write("")

        draft = os.path.join(tmpdir, "draft.md")
        make_draft(draft, "<!-- batch_01 start -->\n...\n<!-- batch_01 end -->\n")

        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/validate_translation.py",
             "--draft", draft, "--batches", batches_dir, "--images", images_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "BATCH_COUNT" in result.stderr


def test_validate_glossary_term_present():
    """Glossary term found in draft → PASS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = os.path.join(tmpdir, "images")
        os.makedirs(images_dir)

        batches_dir = os.path.join(tmpdir, "batches")
        os.makedirs(batches_dir)

        draft = os.path.join(tmpdir, "draft.md")
        make_draft(draft, "This document mentions soft start technology.\n")

        glossary = os.path.join(tmpdir, "glossary.md")
        with open(glossary, "w", encoding="utf-8") as f:
            f.write("| Source Term | Translation |\n")
            f.write("|-------------|-------------|\n")
            f.write("| soft start  | term1       |\n")

        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/validate_translation.py",
             "--draft", draft, "--batches", batches_dir, "--images", images_dir,
             "--glossary", glossary],
            capture_output=True, text=True,
        )
        assert result.returncode == 0


def test_validate_glossary_term_missing():
    """Glossary term NOT in draft → FAIL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = os.path.join(tmpdir, "images")
        os.makedirs(images_dir)

        batches_dir = os.path.join(tmpdir, "batches")
        os.makedirs(batches_dir)

        draft = os.path.join(tmpdir, "draft.md")
        make_draft(draft, "This document contains no matching terms.\n")

        glossary = os.path.join(tmpdir, "glossary.md")
        with open(glossary, "w", encoding="utf-8") as f:
            f.write("| Source Term | Translation |\n")
            f.write("|-------------|-------------|\n")
            f.write("| rare_term   | term2       |\n")

        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/validate_translation.py",
             "--draft", draft, "--batches", batches_dir, "--images", images_dir,
             "--glossary", glossary],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "GLOSSARY" in result.stderr


def test_validate_no_batches_dir():
    """Graceful error when batches dir is missing."""
    result = subprocess.run(
        [sys.executable, "skills/pdf-translate/validate_translation.py",
         "--draft", "/tmp/nonexistent.md", "--batches", "/tmp/nonexistent", "--images", "/tmp/nonexistent"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
