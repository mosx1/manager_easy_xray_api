"""Load config.ini from a fixed path (Docker: /fastapiapp/config.ini)."""

from __future__ import annotations

import os
from configparser import ConfigParser
from functools import lru_cache
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent


def config_ini_path() -> Path:
    override = os.environ.get("CONFIG_INI", "").strip()
    if override:
        return Path(override)
    return APP_ROOT / "config.ini"


@lru_cache(maxsize=1)
def load_config() -> ConfigParser:
    path = config_ini_path()
    if not path.is_file():
        raise RuntimeError(
            f"Config file not found: {path}. "
            "Create config.ini or mount it (e.g. -v /opt/.../config.ini:/fastapiapp/config.ini:ro)."
        )

    parser = ConfigParser()
    read_paths = parser.read(path, encoding="utf-8")
    if not read_paths:
        raise RuntimeError(f"Failed to parse config file: {path}")

    if not parser.has_section("DataBase"):
        raise RuntimeError(
            f"Missing [DataBase] section in {path}. "
            "Add database connection settings (see README)."
        )

    return parser
