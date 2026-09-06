import pathlib


def test_no_langchain_in_requirements():
    req_file = pathlib.Path(__file__).parent.parent / "requirements.txt"
    assert req_file.exists(), "requirements.txt must exist"
    content = req_file.read_text().lower()
    for line in content.splitlines():
        clean = line.strip()
        assert not clean.startswith(
            "langchain"
        ), f"Found forbidden langchain dependency: {clean}"


def test_no_langchain_in_source_code():
    src_dir = pathlib.Path(__file__).parent.parent / "src"
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text()
        assert "import langchain" not in text, f"Found langchain import in {py_file}"
        assert "from langchain" not in text, f"Found langchain import in {py_file}"


def test_tui_libraries_in_requirements():
    req_file = pathlib.Path(__file__).parent.parent / "requirements.txt"
    content = req_file.read_text().lower()
    lines = [line.strip() for line in content.splitlines()]
    assert any(
        "rich" in line for line in lines
    ), "rich must be listed in requirements.txt"
    assert any(
        "prompt_toolkit" in line or "prompt-toolkit" in line for line in lines
    ), "prompt_toolkit must be listed in requirements.txt"


def test_tui_libraries_importable():
    import prompt_toolkit
    import rich

    assert rich is not None
    assert prompt_toolkit is not None
