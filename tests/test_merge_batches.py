import os
import subprocess
import sys
import tempfile


def make_translated_batch(batches_dir, batch_id, content):
    """Create a mock translated batch markdown file."""
    path = os.path.join(batches_dir, f"batch_{batch_id:02d}_translated.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def test_merge_batches_basic():
    """Two batches → one merged file with separators."""
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        os.makedirs(batches_dir)
        make_translated_batch(batches_dir, 1, "# Chapter 1\nContent A\n")
        make_translated_batch(batches_dir, 2, "# Chapter 2\nContent B\n")
        output_path = os.path.join(tmpdir, "merged.md")

        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/merge_batches.py",
             "--batches", batches_dir, "--output", output_path],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(output_path)

        with open(output_path, encoding="utf-8") as f:
            merged = f.read()
        assert "Chapter 1" in merged
        assert "Chapter 2" in merged
        assert "batch_01 start" in merged
        assert "batch_02 start" in merged
        assert "batch_01 end" in merged
        assert "batch_02 end" in merged
        assert merged.index("Chapter 1") < merged.index("Chapter 2")


def test_merge_batches_sorted_order():
    """Batch files merged in numeric order regardless of glob order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        os.makedirs(batches_dir)
        make_translated_batch(batches_dir, 3, "THREE\n")
        make_translated_batch(batches_dir, 1, "ONE\n")
        make_translated_batch(batches_dir, 2, "TWO\n")
        output_path = os.path.join(tmpdir, "merged.md")

        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/merge_batches.py",
             "--batches", batches_dir, "--output", output_path],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

        with open(output_path, encoding="utf-8") as f:
            merged = f.read()
        idx1 = merged.index("ONE")
        idx2 = merged.index("TWO")
        idx3 = merged.index("THREE")
        assert idx1 < idx2 < idx3


def test_merge_batches_no_batches_dir():
    """Fails gracefully when batches dir does not exist."""
    result = subprocess.run(
        [sys.executable, "skills/pdf-translate/merge_batches.py",
         "--batches", "/nonexistent/path", "--output", "/tmp/out.md"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert ("error" in result.stderr.lower() or "batches directory not found" in result.stderr.lower())


def test_merge_batches_help():
    """--help prints usage info with key terms."""
    result = subprocess.run(
        [sys.executable, "skills/pdf-translate/merge_batches.py", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "merge" in result.stdout.lower()
