import importlib.util
from pathlib import Path


def test_agent_assets_validator_passes():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "validate_agent_assets.py"
    spec = importlib.util.spec_from_file_location("validate_agent_assets", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.main() == 0
