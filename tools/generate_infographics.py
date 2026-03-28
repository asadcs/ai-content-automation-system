"""
generate_infographics.py — Generate newsletter infographic images using kie.ai and NanoBanan APIs.

Usage:
    python tools/generate_infographics.py --prompts-json .tmp/image_prompts.json [--output-dir .tmp/] [--theme light]

Prompts JSON format:
    [
      {"id": "img_01", "prompt": "Infographic showing AI adoption rates by industry...", "api": "kieai"},
      {"id": "img_02", "prompt": "Hero image for newsletter about quantum computing...", "api": "nanobanan"}
    ]

The "api" field is optional. If omitted, defaults to "kieai". Falls back to Pillow stat-card if both APIs fail.
"""

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.utils.helpers import load_env, load_json, setup_logger, TMP_DIR

log = setup_logger("generate_infographics")

# Brand colors
BRAND_TEAL = "#00C9A7"
BRAND_NAVY = "#1A2332"
BRAND_LIGHT = "#F5FFFE"

# ─── kie.ai ───────────────────────────────────────────────────────────────────

KIEAI_BASE = "https://api.kie.ai"
KIEAI_GENERATE_ENDPOINT = f"{KIEAI_BASE}/api/v1/gpt4o-image/generate"
KIEAI_TASK_ENDPOINT = f"{KIEAI_BASE}/api/v1/gpt4o-image/task"


def kieai_generate(prompt: str, api_key: str, size: str = "3:2") -> list[str]:
    """Submit a kie.ai generation task and poll for result. Returns list of image URLs."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "size": size}

    log.info(f"[kie.ai] Submitting task: {prompt[:60]}...")
    resp = requests.post(KIEAI_GENERATE_ENDPOINT, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    if data.get("code") != 200:
        raise ValueError(f"kie.ai error: {data.get('msg', 'unknown')}")

    task_id = data["data"]["taskId"]
    log.info(f"[kie.ai] Task submitted: {task_id} — polling for result...")

    # Poll until completed (up to 3 minutes)
    for attempt in range(36):
        time.sleep(5)
        status_resp = requests.get(
            f"{KIEAI_TASK_ENDPOINT}/{task_id}",
            headers=headers,
            timeout=30,
        )
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            if status_data.get("code") == 200:
                result = status_data.get("data", {})
                status = result.get("status", "")
                if status == "completed" or result.get("info", {}).get("result_urls"):
                    urls = result.get("info", {}).get("result_urls", [])
                    log.info(f"[kie.ai] Task complete. Got {len(urls)} image(s).")
                    return urls
                elif status == "failed":
                    raise ValueError(f"kie.ai task failed: {result}")
        log.info(f"[kie.ai] Still processing... (attempt {attempt + 1}/36)")

    raise TimeoutError("kie.ai task did not complete within 3 minutes")


# ─── NanoBanan ────────────────────────────────────────────────────────────────

NANOBANAN_BASE = "https://www.nananobanana.com/api/v1"
NANOBANAN_GENERATE = f"{NANOBANAN_BASE}/generate"


def nanobanan_generate(prompt: str, api_key: str) -> list[str]:
    """Call NanoBanan in sync mode. Returns list of image URLs."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "mode": "sync"}

    log.info(f"[NanoBanan] Generating: {prompt[:60]}...")
    resp = requests.post(NANOBANAN_GENERATE, json=payload, headers=headers, timeout=90)
    resp.raise_for_status()

    data = resp.json()
    urls = data.get("imageUrls") or data.get("output") or []
    if isinstance(urls, str):
        urls = [urls]
    log.info(f"[NanoBanan] Got {len(urls)} image(s).")
    return urls


# ─── Pillow fallback ──────────────────────────────────────────────────────────

def pillow_stat_card(prompt: str, output_path: Path) -> Path:
    """Generate a branded stat-callout card using Pillow when APIs are unavailable."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 800, 450
    img = Image.new("RGB", (W, H), color=BRAND_LIGHT)
    draw = ImageDraw.Draw(img)

    # Teal header bar
    teal_rgb = tuple(int(BRAND_TEAL.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    navy_rgb = tuple(int(BRAND_NAVY.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    draw.rectangle([(0, 0), (W, 12)], fill=teal_rgb)
    draw.rectangle([(0, H - 12), (W, H)], fill=teal_rgb)

    # Wrap prompt text as the stat card body
    lines = []
    words = prompt.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 50:
            line = f"{line} {word}".strip()
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large

    y = 80
    for i, text_line in enumerate(lines[:3]):
        color = teal_rgb if i == 0 else navy_rgb
        draw.text((60, y), text_line, font=font_large if i == 0 else font_small, fill=color)
        y += 55 if i == 0 else 35

    draw.text((60, H - 50), "Xerxes.AI Newsletter", font=font_small, fill=(138, 155, 176))

    img.save(output_path, "PNG")
    log.info(f"[Pillow fallback] Stat card saved: {output_path}")
    return output_path


# ─── Download helper ──────────────────────────────────────────────────────────

def download_image(url: str, dest_path: Path) -> Path:
    """Download image from URL to dest_path."""
    with urllib.request.urlopen(url, timeout=30) as response:
        dest_path.write_bytes(response.read())
    return dest_path


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate newsletter infographics via AI image APIs")
    parser.add_argument("--prompts-json", required=True, help="Path to JSON file with prompt list")
    parser.add_argument("--output-dir", default=None, help="Directory for PNG output (default: .tmp/)")
    parser.add_argument("--theme", default="light", choices=["light", "dark"])
    args = parser.parse_args()

    env = load_env([])  # Keys are optional — we gracefully fall back
    kieai_key = __import__("os").getenv("KIE_AI_API_KEY", "")
    nanobanan_key = __import__("os").getenv("NANOBANAN_API_KEY", "")

    output_dir = Path(args.output_dir) if args.output_dir else TMP_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    prompts = load_json(args.prompts_json)
    if not isinstance(prompts, list):
        log.error("prompts-json must be a JSON array")
        sys.exit(1)

    output_files = []

    for item in prompts:
        img_id = item.get("id", f"img_{len(output_files):02d}")
        prompt = item.get("prompt", "")
        preferred_api = item.get("api", "kieai").lower()
        dest = output_dir / f"{img_id}.png"

        success = False

        # Try preferred API first
        apis_to_try = [preferred_api] + (["nanobanan"] if preferred_api == "kieai" else ["kieai"])

        for api in apis_to_try:
            if success:
                break
            try:
                if api == "kieai":
                    if not kieai_key:
                        log.warning("[kie.ai] KIE_AI_API_KEY not set — skipping")
                        continue
                    urls = kieai_generate(prompt, kieai_key)
                    if urls:
                        download_image(urls[0], dest)
                        success = True
                elif api == "nanobanan":
                    if not nanobanan_key:
                        log.warning("[NanoBanan] NANOBANAN_API_KEY not set — skipping")
                        continue
                    urls = nanobanan_generate(prompt, nanobanan_key)
                    if urls:
                        download_image(urls[0], dest)
                        success = True
            except Exception as e:
                log.warning(f"[{api}] Failed for {img_id}: {e}")

        if not success:
            log.warning(f"All APIs failed for {img_id} — using Pillow fallback")
            pillow_stat_card(prompt, dest)

        output_files.append(str(dest))
        log.info(f"[green]Saved:[/green] {dest}")

    # Print JSON list of output paths to stdout for tool chaining
    print(json.dumps(output_files))


if __name__ == "__main__":
    main()
