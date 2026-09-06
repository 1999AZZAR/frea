from src.cli import parse_args


def test_parse_args_default_interactive():
    """Verify default invocation without args defaults to interactive mode."""
    config = parse_args([])
    assert config.prompt is None
    assert config.is_interactive is True
    assert config.yes is False


def test_parse_args_headless_prompt():
    """Verify -p / --prompt / --run sets non-interactive prompt."""
    config1 = parse_args(["-p", "write a hello world script"])
    assert config1.prompt == "write a hello world script"
    assert config1.is_interactive is False

    config2 = parse_args(["--run", "check git status"])
    assert config2.prompt == "check git status"
    assert config2.is_interactive is False


def test_parse_args_flags():
    """Verify --yes and --model flags are correctly parsed."""
    config = parse_args(["-p", "list files", "--yes", "--model", "groq/llama-3.3-70b"])
    assert config.prompt == "list files"
    assert config.yes is True
    assert config.model == "groq/llama-3.3-70b"


def test_parse_args_config_flag():
    """Verify -c and --config flags are parsed."""
    config1 = parse_args(["-c", "/tmp/custom_config.json"])
    assert config1.config_path == "/tmp/custom_config.json"

    config2 = parse_args(["--config", "my_config.json"])
    assert config2.config_path == "my_config.json"


def test_parse_args_default_model_none():
    """Verify model is None by default to allow fallback to config.json."""
    config = parse_args([])
    assert config.model is None
