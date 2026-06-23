import json
import os
from functools import lru_cache
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT_DIR / "config" / "config.json"


@lru_cache(maxsize=1)
def _load_config() -> dict:
    with CONFIG_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def get_env() -> str:
    return os.getenv("TEST_ENV", "qa").lower()


def get_config(key: str, default=None):
    env = get_env()
    config = _load_config()
    env_config = config.get(env, config["default"])
    return env_config.get(key, config["default"].get(key, default))


def get_base_url() -> str:
    return os.getenv("BASE_URL", get_config("base_url")).rstrip("/")


def get_timeout() -> int:
    return int(os.getenv("REQUEST_TIMEOUT", get_config("timeout", 10)))


def should_auto_start_mock_api() -> bool:
    value = os.getenv("AUTO_START_MOCK_API")
    if value is not None:
        return value.lower() in {"1", "true", "yes"}
    return bool(get_config("auto_start_mock_api", True))
