"""
generate_newsletter_html.py — Render a Jinja2 newsletter template with content + images.

Usage:
    python tools/generate_newsletter_html.py --content .tmp/content.json [--images-dir .tmp/] [--output .tmp/newsletter.html]

Content JSON schema:
{
  "subject": "Main subject line",
  "subject_variants": ["Variant A", "Variant B", "Variant C"],
  "preview_text": "Short preview text shown in email clients",
  "date": "March 28, 2026",
  "issue_number": null,
  "audience": "tech professionals",
  "tldr": "3-sentence summary of the newsletter",
  "sections": [
    {
      "heading": "Section Title",
      "body_html": "<p>HTML body content...</p>",
      "image_file": "img_01.png",  // filename in images-dir (optional)
      "sources": [
        {"title": "Source name", "url": "https://...", "credibility": "high"}
      ]
    }
  ],
  "closing": "Thanks for reading. — The Xerxes.AI Team",
  "cta": {"text": "Explore More", "url": "https://xerxes.ai"},
  "footer": {
    "company": "Xerxes.AI",
    "address": "123 Main St, City, State 00000",
    "unsubscribe_url": "#"
  }
}
"""

import argparse
import base64
import sys
from pathlib import Path

import textstat
from jinja2 import Environment, FileSystemLoader
from premailer import transform

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.utils.helpers import load_json, save_json, get_output_path, setup_logger, PROJECT_ROOT

log = setup_logger("generate_newsletter_html")

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
BRAND_ASSETS_DIR = PROJECT_ROOT / "brand_assets"
LOGO_PATH = BRAND_ASSETS_DIR / "Xerxes PNG.png"


def encode_image(path: Path) -> str | None:
    """Base64-encode an image file. Returns None if file doesn't exist."""
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    log.warning(f"Image not found, skipping: {path}")
    return None


def check_readability(sections: list) -> None:
    """Compute Flesch-Kincaid grade level from all section body text and warn if high."""
    import re
    all_text = " ".join(
        re.sub(r"<[^>]+>", " ", s.get("body_html", ""))
        for s in sections
    )
    if len(all_text.strip()) < 100:
        return
    grade = textstat.flesch_kincaid_grade(all_text)
    reading_ease = textstat.flesch_reading_ease(all_text)
    log.info(f"Readability: Flesch-Kincaid Grade {grade:.1f} | Ease {reading_ease:.0f}/100")
    if grade > 12:
        log.warning(
            f"[yellow]Reading level is Grade {grade:.1f} — consider simplifying sentences for broader accessibility.[/yellow]"
        )


def main():
    parser = argparse.ArgumentParser(description="Render newsletter HTML from content JSON")
    parser.add_argument("--content", required=True, help="Path to content JSON file")
    parser.add_argument("--images-dir", default=None, help="Directory containing chart/image PNGs (default: .tmp/)")
    parser.add_argument("--template", default=None, help="Path to Jinja2 template (default: tools/templates/newsletter_base.html)")
    parser.add_argument("--output", default=None, help="Output HTML path (default: .tmp/newsletter_{date}.html)")
    args = parser.parse_args()

    content = load_json(args.content)

    images_dir = Path(args.images_dir) if args.images_dir else PROJECT_ROOT / ".tmp"
    template_path = Path(args.template) if args.template else TEMPLATE_DIR / "newsletter_base.html"
    output_path = Path(args.output) if args.output else get_output_path("newsletter", "html")

    # ── Logo ──────────────────────────────────────────────────────────────────
    logo_b64 = encode_image(LOGO_PATH)
    if not logo_b64:
        log.warning("Xerxes logo not found — header will use text fallback")

    # ── Embed images into sections ────────────────────────────────────────────
    sections = content.get("sections", [])
    for section in sections:
        img_file = section.get("image_file")
        if img_file:
            img_path = images_dir / img_file
            b64 = encode_image(img_path)
            section["image_base64"] = b64
        else:
            section["image_base64"] = None

    # ── Readability check ─────────────────────────────────────────────────────
    check_readability(sections)

    # ── Render template ───────────────────────────────────────────────────────
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=False,  # We control HTML — body_html is intentionally raw
    )
    template = env.get_template(template_path.name)

    rendered_html = template.render(
        subject=content.get("subject", "Xerxes.AI Newsletter"),
        subject_variants=content.get("subject_variants", []),
        preview_text=content.get("preview_text", ""),
        date=content.get("date", ""),
        issue_number=content.get("issue_number"),
        audience=content.get("audience", ""),
        tldr=content.get("tldr", ""),
        sections=sections,
        closing=content.get("closing", ""),
        cta=content.get("cta", {}),
        footer=content.get("footer", {}),
        logo_base64=logo_b64,
    )

    # ── Inline CSS via premailer (Gmail compatibility) ────────────────────────
    try:
        inlined_html = transform(
            rendered_html,
            remove_classes=False,
            keep_style_tags=True,  # Keeps media queries intact
            cssutils_logging_level=40,  # Suppress cssutils warnings
        )
    except Exception as e:
        log.warning(f"premailer CSS inlining failed ({e}) — using raw template output")
        inlined_html = rendered_html

    # ── Write output ──────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(inlined_html, encoding="utf-8")

    size_kb = output_path.stat().st_size / 1024
    log.info(f"[green]Newsletter rendered:[/green] {output_path} ({size_kb:.1f} KB)")

    if size_kb < 5:
        log.warning("Output file is very small — double-check content JSON has populated sections")

    print(str(output_path))  # stdout for tool chaining


if __name__ == "__main__":
    main()
