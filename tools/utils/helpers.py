"""Shared utilities for all newsletter automation tools."""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
import logging

console = Console()

# Project root is two levels up from this file (tools/utils/helpers.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"


def load_env(required_keys: list[str] | None = None) -> dict:
    """Load .env from project root. Raises if any required keys are missing or empty."""
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=env_path)

    if required_keys:
        missing = [k for k in required_keys if not os.getenv(k)]
        if missing:
            console.print(f"[red]ERROR:[/red] Missing required .env keys: {', '.join(missing)}")
            console.print(f"[dim]Expected in: {env_path}[/dim]")
            sys.exit(1)

    return {k: os.getenv(k, "") for k in (required_keys or [])}


def save_json(data: dict | list, path: str | Path) -> Path:
    """Atomically write pretty-printed JSON to path. Creates parent dirs if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp.json")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp_path.replace(path)
    return path


def load_json(path: str | Path) -> dict | list:
    """Load JSON from path with a clear error if file is missing."""
    path = Path(path)
    if not path.exists():
        console.print(f"[red]ERROR:[/red] File not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def slugify(text: str) -> str:
    """Convert a topic string into a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:60]


def get_output_path(prefix: str, ext: str) -> Path:
    """Return .tmp/{prefix}_{YYYYMMDD_HHMM}.{ext}, creating .tmp/ if needed."""
    TMP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{prefix}_{timestamp}.{ext.lstrip('.')}"
    return TMP_DIR / filename


def setup_logger(name: str) -> logging.Logger:
    """Return a rich-formatted logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_path=False, markup=True)],
    )
    return logging.getLogger(name)
