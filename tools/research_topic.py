"""
research_topic.py — Research a newsletter topic using the Perplexity API.

Usage:
    python tools/research_topic.py --topic "AI agents in healthcare" [--audience "tech professionals"] [--output .tmp/research.json]
"""

import argparse
import sys
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.utils.helpers import load_env, save_json, get_output_path, setup_logger, slugify

log = setup_logger("research_topic")

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar"

RESEARCH_PROMPT = """\
You are a research assistant for a professional newsletter. Research the following topic thoroughly and return a structured JSON response.

Topic: {topic}
Target audience: {audience}

Return ONLY valid JSON (no markdown, no code blocks) in this exact structure:
{{
  "topic": "{topic}",
  "audience": "{audience}",
  "summary": "3-4 sentence executive summary of the topic",
  "key_facts": [
    "Concrete fact or finding #1",
    "Concrete fact or finding #2",
    "Concrete fact or finding #3",
    "Concrete fact or finding #4",
    "Concrete fact or finding #5"
  ],
  "statistics": [
    {{"value": "74%", "context": "of CEOs plan to increase AI investment in 2025", "source": "McKinsey Global Survey"}},
    {{"value": "$X billion", "context": "market size / growth metric", "source": "source name"}}
  ],
  "expert_quotes": [
    {{"quote": "Exact or paraphrased quote", "author": "Name, Title, Organization"}}
  ],
  "key_themes": ["Theme 1", "Theme 2", "Theme 3"],
  "controversies_or_challenges": "What are the main debates, risks, or obstacles in this space?",
  "future_outlook": "What is expected to happen in the next 1-3 years?",
  "sources": [
    {{"title": "Article or report title", "url": "https://...", "credibility": "high"}},
    {{"title": "Article or report title", "url": "https://...", "credibility": "medium"}}
  ]
}}

Ensure statistics are specific and cited. Prefer recent data (2024-2026). Credibility is "high" for .gov, .edu, Reuters, AP, Nature, McKinsey, etc.; otherwise "medium".\
"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.RequestException),
)
def call_perplexity(topic: str, audience: str, api_key: str) -> dict:
    """Call Perplexity API and return parsed JSON research data."""
    prompt = RESEARCH_PROMPT.format(topic=topic, audience=audience)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a research assistant. Return only valid JSON, no markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 3000,
    }

    response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers, timeout=60)

    if response.status_code == 429:
        log.warning("Perplexity rate limit hit — will retry with backoff")
        response.raise_for_status()
    elif response.status_code != 200:
        log.error(f"Perplexity API error {response.status_code}: {response.text[:300]}")
        response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if Perplexity wraps in them
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    import json
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse Perplexity response as JSON: {e}")
        log.error(f"Raw response:\n{content[:500]}")
        raise ValueError(f"Perplexity returned non-JSON: {e}") from e


def main():
    parser = argparse.ArgumentParser(description="Research a newsletter topic via Perplexity API")
    parser.add_argument("--topic", required=True, help="The topic to research")
    parser.add_argument("--audience", default="general professionals", help="Target audience description")
    parser.add_argument("--output", default=None, help="Output JSON path (default: .tmp/research_{slug}_{date}.json)")
    args = parser.parse_args()

    env = load_env(["PERPLEXITY_API_KEY"])
    api_key = env["PERPLEXITY_API_KEY"]

    output_path = args.output or get_output_path(f"research_{slugify(args.topic)}", "json")

    log.info(f"Researching: [bold]{args.topic}[/bold]")
    log.info(f"Audience: {args.audience}")

    research = call_perplexity(args.topic, args.audience, api_key)
    research["researched_at"] = __import__("datetime").datetime.now().isoformat()

    save_json(research, output_path)
    log.info(f"[green]Research saved:[/green] {output_path}")
    print(str(output_path))  # stdout for tool chaining


if __name__ == "__main__":
    main()
