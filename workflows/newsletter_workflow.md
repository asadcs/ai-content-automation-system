# Newsletter Workflow

## Objective
Research a topic, write a polished HTML newsletter in the Xerxes.AI brand, generate AI infographics, and deliver via Gmail.

## One-Time Setup
Before the first run, ensure:
1. `.env` has: `PERPLEXITY_API_KEY`, `GMAIL_SENDER_ADDRESS`, `GMAIL_RECIPIENT_ADDRESS`
2. Optional: `KIE_AI_API_KEY`, `NANOBANAN_API_KEY` (infographics fall back to Pillow if unset)
3. `credentials.json` in project root (Google Cloud → Gmail API → OAuth client secret)
4. Run `pip install jinja2 premailer textstat pillow google-api-python-client google-auth-httplib2 google-auth-oauthlib beautifulsoup4 requests tenacity rich python-dotenv` if not already done

---

## Phase 0: Intake

Collect from the user before starting. Ask for anything not provided:

| Input | Required | Default |
|---|---|---|
| `topic` | Yes | — |
| `audience` | No | "general professionals" |
| `tone` | No | "informative and engaging, not overly formal" |
| `length` | No | "standard" (5 sections) |
| `recipient_email` | No | GMAIL_RECIPIENT_ADDRESS from .env |
| `issue_number` | No | omit if not a series |

Length guide: short = 3 sections, standard = 5 sections, deep = 7 sections.

---

## Phase 1: Research

Run the research tool:

```
python tools/research_topic.py --topic "{topic}" --audience "{audience}"
```

- Prints the output JSON path to stdout
- Read the output JSON and internalize all findings
- Note which statistics are specific and quotable
- Note which data points are chartable (percentages, comparisons, trends)
- If a major angle seems missing, the tool can be run again with a more specific sub-topic

**Rate limit note:** Perplexity sonar model — 100 requests/minute on Pro plan. Not a concern for single newsletter runs.

---

## Phase 2: Content Architecture (reasoning step — no tool call)

Before writing, plan the structure:

1. Identify the **5 most newsworthy/useful findings** (or 3 for short / 7 for deep)
2. Order sections: most important or surprising first (inverted pyramid)
3. Draft the **TL;DR** — exactly 3 sentences: what's happening, why it matters, what's next
4. Draft the **subject line** — then 2 A/B variants:
   - Variant A: curiosity hook ("Why X is changing everything about Y")
   - Variant B: direct benefit ("How to use X to achieve Y")
   - Variant C: question ("Is X really as powerful as they say?")
5. Assign which sections get an infographic (max 3 images per newsletter — pick the most visual-friendly stats)
6. Write **image prompts** for each infographic — be specific and visual: "Clean infographic showing 74% adoption rate, teal and navy color scheme, Xerxes.AI brand style, professional, minimal, data-forward"

---

## Phase 3: Infographic Generation

Write the image prompt list to `.tmp/image_prompts.json`:

```json
[
  {"id": "img_01", "prompt": "...", "api": "kieai"},
  {"id": "img_02", "prompt": "...", "api": "nanobanan"}
]
```

The `api` field is optional (defaults to `kieai`). Use `nanobanan` for hero/decorative images, `kieai` for data-forward infographics.

Run:
```
python tools/generate_infographics.py --prompts-json .tmp/image_prompts.json
```

- Prints a JSON list of output PNG paths
- Verify PNGs exist in `.tmp/`
- If an image failed and fell back to Pillow, note this — you may want to retry or omit the image

---

## Phase 4: Content Writing (Claude generation — no tool call)

Write the full `content.json` to `.tmp/content_{slug}_{date}.json`:

```json
{
  "subject": "Primary subject line",
  "subject_variants": ["Variant A", "Variant B", "Variant C"],
  "preview_text": "Short preview text (50-90 chars) shown in email client inbox",
  "date": "March 28, 2026",
  "issue_number": null,
  "audience": "tech professionals",
  "tldr": "Three-sentence summary here.",
  "sections": [
    {
      "heading": "Section heading",
      "body_html": "<p>Section body using HTML. Use <strong>bold</strong> for key terms. Use <ul><li>lists</li></ul> for enumerated points.</p><p>3-5 paragraphs. Keep sentences under 25 words.</p>",
      "image_file": "img_01.png",
      "sources": [
        {"title": "Source name", "url": "https://...", "credibility": "high"}
      ]
    }
  ],
  "closing": "Thanks for reading — see you next week.\n\n— The Xerxes.AI Team",
  "cta": {"text": "Explore More at Xerxes.AI", "url": "https://xerxes.ai"},
  "footer": {
    "company": "Xerxes.AI",
    "address": "",
    "unsubscribe_url": "#"
  }
}
```

**Writing rules:**
- Tone: match the user's requested tone; default is professional but not stiff
- Each section: 3-5 paragraphs, concrete and specific, no filler
- Only cite statistics from the research JSON — do not invent data
- Keep sentences under 25 words average for readability score ≤ 12
- body_html uses only: `<p>`, `<strong>`, `<em>`, `<ul>`, `<li>`, `<a href="...">`
- Link sources inline in body where natural, and also list in the `sources` array
- The `image_file` must exactly match a PNG filename that was generated in Phase 3

---

## Phase 5: HTML Render

```
python tools/generate_newsletter_html.py --content .tmp/content_{slug}_{date}.json --images-dir .tmp/
```

- Prints the output HTML path to stdout
- Note the readability grade level logged to console — if above 12, revise the densest sections

Open preview:
```
python tools/preview_newsletter.py --file .tmp/newsletter_{date}_{time}.html
```

**Verify in browser:**
- [ ] Xerxes.AI logo renders in header and footer
- [ ] Teal accent color on headings, TL;DR border, and CTA button
- [ ] Images load (they are base64-embedded — if broken, check the image_file filenames)
- [ ] All sections present with correct text
- [ ] Sources section visible under relevant sections
- [ ] CTA button correct

Report the file path to the user and ask if they'd like any changes before sending.

---

## Phase 6: Send via Gmail

Only proceed after user confirms they're happy with the preview.

Default (draft — always start here):
```
python tools/send_gmail.py --html-file .tmp/newsletter_{date}.html --subject "{primary subject}" [--to recipient@example.com]
```

This saves a draft in Gmail. The user can review it in their Gmail drafts and send manually.

To send programmatically (only with explicit user instruction):
```
python tools/send_gmail.py --html-file .tmp/newsletter_{date}.html --subject "{primary subject}" --send-now
```

**IMPORTANT:** Never pass `--send-now` without explicit user confirmation. Always default to draft mode.

On first run, Gmail OAuth will open a browser window — this is expected. After consent, `token.json` is cached and future runs are silent.

---

## Series Memory (optional but recommended)

After each successful newsletter, append to `.tmp/newsletter_series.json`:

```json
[
  {
    "issue_number": 1,
    "date": "2026-03-28",
    "topic": "AI agents in healthcare",
    "subject_used": "How AI agents are replacing hospital admin",
    "file": ".tmp/newsletter_20260328_1430.html"
  }
]
```

Before starting a new newsletter, read this file to avoid repeating topics or angles covered in recent issues.

---

## Error Handling

| Error | Diagnosis | Resolution |
|---|---|---|
| Perplexity 401 | Bad API key | Check `PERPLEXITY_API_KEY` in `.env` |
| Perplexity 429 | Rate limit | Wait 60s and retry; reduce to 1 API call if persistent |
| Perplexity returns non-JSON | Model compliance issue | Re-run; if persistent, adjust prompt to be more explicit |
| kie.ai task timeout | API slow or overloaded | Retry once; fall back to NanoBanan or Pillow |
| NanoBanan 401 | Bad API key | Check `NANOBANAN_API_KEY` in `.env` |
| premailer CSS error | Malformed HTML in body_html | Fix HTML tags in content.json and re-render |
| Gmail OAuth 401 | Token expired | Delete `token.json` and re-run (will re-prompt browser) |
| Gmail 403 | Scope or API not enabled | Enable Gmail API in Google Cloud Console |
| HTML file < 5KB | Content sections not rendered | Check content.json has populated `sections` array |
| Logo not showing | Wrong path | Verify `brand_assets/Xerxes PNG.png` exists |
