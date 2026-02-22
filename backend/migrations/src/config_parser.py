import json
from pathlib import Path


def parse_config_file(file_path: Path) -> dict:
    """Parse the JSON configuration file and return the configuration dictionary.

    Args:
        file_path (Path): Path to the JSON configuration file.

    Returns:
        dict: Configuration dictionary.

    """
    with open(file_path, "r") as file:
        config = json.load(file)
    return config
