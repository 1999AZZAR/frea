from pathlib import Path
from src.tools import (
    glob,
    grep,
    list_directory,
    read_file,
    write_file,
    patch_file,
)


def test_read_file_full_and_sliced(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("line 1\nline 2\nline 3\nline 4\nline 5\n", encoding="utf-8")

    # Read all lines with line numbers
    res = read_file(str(sample))
    assert res.success is True
    assert "1: line 1" in res.output
    assert "5: line 5" in res.output

    # Read with offset (1-based) and limit
    res_sliced = read_file(str(sample), offset=2, limit=2)
    assert res_sliced.success is True
    assert "2: line 2" in res_sliced.output
    assert "3: line 3" in res_sliced.output
    assert "1: line 1" not in res_sliced.output
    assert "4: line 4" not in res_sliced.output


def test_read_file_nonexistent():
    res = read_file("/nonexistent/file/path/here.txt")
    assert res.success is False
    assert "File not found" in res.error or "not found" in res.error.lower()


def test_write_file_new_and_overwrite(tmp_path: Path):
    target = tmp_path / "subdir" / "new_file.txt"

    # Writing to new file creates parent directories
    res = write_file(str(target), "Hello Frea\nLine 2")
    assert res.success is True
    assert target.is_file()
    assert target.read_text() == "Hello Frea\nLine 2"

    # Writing existing without overwrite fails
    res_fail = write_file(str(target), "New content", overwrite=False)
    assert res_fail.success is False
    assert "already exists" in res_fail.error

    # Writing with overwrite=True succeeds
    res_overwrite = write_file(str(target), "Overwritten!", overwrite=True)
    assert res_overwrite.success is True
    assert target.read_text() == "Overwritten!"


def test_patch_file_create_new(tmp_path: Path):
    target = tmp_path / "created.txt"
    # When old_text is empty, patch_file creates the file
    res = patch_file(str(target), old_text="", new_text="Brand new content")
    assert res.success is True
    assert target.is_file()
    assert target.read_text() == "Brand new content"


def test_patch_file_exact_replacement(tmp_path: Path):
    target = tmp_path / "patch_me.txt"
    target.write_text("apple\nbanana\ncherry\n", encoding="utf-8")

    res = patch_file(str(target), old_text="banana", new_text="blueberry")
    assert res.success is True
    assert "blueberry" in target.read_text()
    assert "banana" not in target.read_text()


def test_patch_file_errors_on_missing_or_duplicate(tmp_path: Path):
    target = tmp_path / "errors.txt"
    target.write_text("dup\nsomething\ndup\n", encoding="utf-8")

    # Missing old_text
    res_missing = patch_file(str(target), old_text="not_here", new_text="x")
    assert res_missing.success is False
    assert "not found" in res_missing.error.lower()

    # Duplicate old_text
    res_dup = patch_file(str(target), old_text="dup", new_text="x")
    assert res_dup.success is False
    assert "2 times" in res_dup.error or "multiple" in res_dup.error.lower()


def test_list_directory(tmp_path: Path):
    (tmp_path / "file1.txt").write_text("123")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "file2.py").write_text("print(1)")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "secret.txt").write_text("shh")

    res = list_directory(str(tmp_path))
    assert res.success is True
    assert "sub/" in res.output
    assert "file1.txt" in res.output
    assert ".hidden" not in res.output


def test_grep_and_glob(tmp_path: Path):
    code_dir = tmp_path / "src"
    code_dir.mkdir()
    (code_dir / "app.py").write_text("def hello_world():\n    return 42\n")
    (code_dir / "util.py").write_text("def helper():\n    pass\n")

    # Grep literal
    res_grep = grep("hello_world", path=str(tmp_path))
    assert res_grep.success is True
    assert "app.py:1:" in res_grep.output
    assert "def hello_world():" in res_grep.output

    # Grep regex
    res_regex = grep(r"def \w+\(\):", path=str(tmp_path), is_regex=True)
    assert res_regex.success is True
    assert "app.py:1:" in res_regex.output
    assert "util.py:1:" in res_regex.output

    # Glob
    res_glob = glob("*.py", path=str(tmp_path))
    assert res_glob.success is True
    assert "app.py" in res_glob.output
    assert "util.py" in res_glob.output
