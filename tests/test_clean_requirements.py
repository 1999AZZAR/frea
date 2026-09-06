import pathlib
import sys
from unittest.mock import patch


def test_requirements_only_necessary_packages():
    req_file = pathlib.Path(__file__).parent.parent / "requirements.txt"
    assert req_file.exists()
    lines = [
        line.strip().lower()
        for line in req_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

    # Exactly 4 production packages needed
    pkg_names = [line.split(">=")[0].split("==")[0].strip() for line in lines]
    forbidden = {"emoji", "fpdf", "fpdf2", "wikipedia-api", "wikipedia", "langchain"}
    for pkg in pkg_names:
        assert (
            pkg not in forbidden
        ), f"Forbidden package found in requirements.txt: {pkg}"

    allowed = {
        "openai",
        "google-generativeai",
        "google.generativeai",
        "rich",
        "prompt_toolkit",
        "prompt-toolkit",
    }
    for pkg in pkg_names:
        assert pkg in allowed, f"Unexpected package in minimal requirements.txt: {pkg}"


def test_dev_requirements_present():
    dev_req = pathlib.Path(__file__).parent.parent / "requirements-dev.txt"
    assert dev_req.exists(), "requirements-dev.txt must exist"
    content = dev_req.read_text().lower()
    assert "pytest" in content


def test_agent_tools_import_without_wikipediaapi():
    # Simulate wikipediaapi not installed
    with patch.dict(sys.modules, {"wikipediaapi": None}):
        import src.agent_tools as tools

        # Core utility tools must remain callable
        assert tools.calc("2 + 2") == "4"
        assert (
            "No Wikipedia module" in tools.wiki("Python")
            or "error" in tools.wiki("Python").lower()
        )
