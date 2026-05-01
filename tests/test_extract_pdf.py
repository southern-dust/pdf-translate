import json
import os
import subprocess
import sys
import tempfile

try:
    import fitz
except ImportError:
    fitz = None


def test_extract_pdf_help():
    """Smoke test: script runs and prints usage."""
    result = subprocess.run(
        [sys.executable, "skills/pdf-translate/extract_pdf.py", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--input" in result.stdout
    assert "--output" in result.stdout


def test_extract_pdf_missing_input():
    """Script fails gracefully when no --input given."""
    result = subprocess.run(
        [sys.executable, "skills/pdf-translate/extract_pdf.py", "--output", "/tmp"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_extract_pdf_behavioral():
    """Creates a minimal PDF and verifies extracted_pages.json structure."""
    if fitz is None:
        import pytest
        pytest.skip("PyMuPDF not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "test.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), "Hello world", fontsize=12)
        doc.save(pdf_path)
        doc.close()

        output_dir = os.path.join(tmpdir, "output")
        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/extract_pdf.py",
             "--input", pdf_path, "--output", output_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

        assert os.path.isdir(output_dir)
        assert os.path.isdir(os.path.join(output_dir, "images"))

        json_path = os.path.join(output_dir, "extracted_pages.json")
        assert os.path.isfile(json_path)

        with open(json_path, "r") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["page"] == 1
        assert "text" in data[0]
        assert "images" in data[0]
        assert isinstance(data[0]["images"], list)
