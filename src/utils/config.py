import json
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_PATH = CONFIG_DIR / "config.json"


# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_api_key(api_key):
    """
    Save or overwrite the Google Maps API key to config.json.
    """
    config = {}

    # Load existing config if present
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    # Check for existing key
    old_key = config.get("google_api_key")
    if old_key:
        action = "overwritten"
    else:
        action = "saved"

    config["google_api_key"] = api_key

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    return action


def load_api_key():
    """
    Load the Google Maps API key from config.json.
    """
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            return config.get("google_api_key")
    return None
