"""
preview_newsletter.py — Open a newsletter HTML file in the system default browser.

Usage:
    python tools/preview_newsletter.py --file .tmp/newsletter_20260328_1430.html
"""

import argparse
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.utils.helpers import setup_logger

log = setup_logger("preview_newsletter")


def main():
    parser = argparse.ArgumentParser(description="Open newsletter HTML in the default browser")
    parser.add_argument("--file", required=True, help="Path to the HTML file to preview")
    args = parser.parse_args()

    path = Path(args.file).resolve()
    if not path.exists():
        log.error(f"File not found: {path}")
        sys.exit(1)

    file_url = path.as_uri()  # Produces file:///C:/... on Windows
    log.info(f"Opening in browser: {file_url}")

    opened = webbrowser.open(file_url)
    if not opened:
        log.warning("Could not open browser automatically.")
        log.info(f"Open manually: {file_url}")
    else:
        log.info("[green]Browser opened.[/green]")


if __name__ == "__main__":
    main()
