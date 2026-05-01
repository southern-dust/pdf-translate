import json
import os
import subprocess
import sys
import tempfile


def make_pages_json(num_pages):
    """Helper: create a temporary extracted_pages.json with `num_pages` pages."""
    pages = [{"page": i + 1, "text": f"Page {i+1} content", "images": []} for i in range(num_pages)]
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pages, f)
    return path


def count_batch_files(batches_dir):
    """Count batch JSON files."""
    return len([f for f in os.listdir(batches_dir) if f.startswith("batch_") and f.endswith(".json")])


def test_split_batches_default_size():
    """30 pages with default size=15 → 2 batches."""
    json_path = make_pages_json(30)
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/split_batches.py",
             "--input", json_path, "--output", batches_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert count_batch_files(batches_dir) == 2
    os.unlink(json_path)


def test_split_batches_custom_size():
    """12 pages with size=5 → 3 batches."""
    json_path = make_pages_json(12)
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/split_batches.py",
             "--input", json_path, "--output", batches_dir, "--size", "5"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert count_batch_files(batches_dir) == 3
    os.unlink(json_path)


def test_split_batches_single_batch_hint():
    """≤5 pages → single batch, prints hint about no parallelism needed."""
    json_path = make_pages_json(3)
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/split_batches.py",
             "--input", json_path, "--output", batches_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert count_batch_files(batches_dir) == 1
        assert "single batch" in result.stdout.lower()
    os.unlink(json_path)


def test_split_batches_zero_pages():
    """Empty pages array → warning and exit code 0."""
    json_path = make_pages_json(0)
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/split_batches.py",
             "--input", json_path, "--output", batches_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "no pages" in result.stdout.lower()
    os.unlink(json_path)


def test_split_batches_help():
    """--help prints usage info with key terms from BATCH_SIZE_HELP."""
    result = subprocess.run(
        [sys.executable, "skills/pdf-translate/split_batches.py", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "dense" in result.stdout.lower()
    assert "guidelines" in result.stdout.lower()


def test_split_batches_invalid_json():
    """Malformed JSON file → clean error, exit code 1."""
    fd, json_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write("not valid json{{{")
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/split_batches.py",
             "--input", json_path, "--output", batches_dir],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stderr.lower()
        assert "json" in result.stderr.lower()
    os.unlink(json_path)


def test_split_batches_size_zero():
    """--size 0 → error, exit code 1."""
    json_path = make_pages_json(5)
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/split_batches.py",
             "--input", json_path, "--output", batches_dir, "--size", "0"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stderr.lower()
    os.unlink(json_path)


def test_split_batches_size_negative():
    """--size -1 → error, exit code 1."""
    json_path = make_pages_json(5)
    with tempfile.TemporaryDirectory() as tmpdir:
        batches_dir = os.path.join(tmpdir, "batches")
        result = subprocess.run(
            [sys.executable, "skills/pdf-translate/split_batches.py",
             "--input", json_path, "--output", batches_dir, "--size", "-1"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stderr.lower()
    os.unlink(json_path)
