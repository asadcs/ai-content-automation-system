# AI Content Automation System – Newsletter Workflow

An end-to-end AI-powered pipeline that automates topic research, structured content generation, infographic creation, and email delivery using modern LLM and API-based workflows.

---

## Overview

This project automates the complete lifecycle of newsletter creation, transforming a single topic input into a fully designed and deliverable HTML newsletter.

The system is built as a modular AI pipeline and demonstrates real-world applications of LLMs, workflow orchestration, and API integration.

---

## Key Capabilities

- Automated topic research using Perplexity API
- Structured HTML content generation using Claude
- AI-generated infographics with fallback support
- Branded email rendering (Xerxes.AI style)
- Gmail API integration with draft-first safety
- Modular and extensible pipeline architecture

---

## System Architecture

```
User Input
   ↓
Research Layer (Perplexity API)
   ↓
Content Planning Layer
   ↓
Generation Layer (Claude)
   ↓
Infographic Generation
   ↓
Rendering Layer (HTML + Styling)
   ↓
Delivery Layer (Gmail API)
```

### Architecture Breakdown

- **Research Layer**
  Collects structured insights and statistics from external APIs

- **Planning Layer**
  Organizes content into sections, TL;DR, and subject lines

- **Generation Layer**
  Uses Claude to generate structured, readable HTML content

- **Rendering Layer**
  Converts structured data into styled HTML emails

- **Delivery Layer**
  Sends emails via Gmail API with draft and send modes

---

## Tech Stack

- Python
- Claude (LLM for content generation)
- Perplexity API (research)
- Gmail API (email delivery)
- Jinja2, Premailer (HTML rendering)
- Pillow / AI APIs (infographics)
- BeautifulSoup (HTML processing)

---

## Workflow

1. Topic input and audience definition
2. Research and data extraction
3. Content planning and structuring
4. Infographic generation
5. HTML newsletter rendering
6. Preview and validation
7. Email delivery via Gmail API

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-content-automation-system.git
cd ai-content-automation-system
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```
PERPLEXITY_API_KEY=your_key
GMAIL_SENDER_ADDRESS=your_email
GMAIL_RECIPIENT_ADDRESS=recipient_email
```

### 4. Add Google credentials

- Place `credentials.json` in the root directory
- Enable Gmail API in Google Cloud Console

---

## Usage

### Step 1: Research Topic

```bash
python tools/research_topic.py --topic "AI agents" --audience "tech professionals"
```

### Step 2: Generate Infographics

```bash
python tools/generate_infographics.py --prompts-json .tmp/image_prompts.json
```

### Step 3: Generate Newsletter HTML

```bash
python tools/generate_newsletter_html.py --content .tmp/content.json --images-dir .tmp/
```

### Step 4: Preview Newsletter

```bash
python tools/preview_newsletter.py --file .tmp/newsletter.html
```

### Step 5: Send via Gmail

```bash
python tools/send_gmail.py --html-file .tmp/newsletter.html --subject "Your Subject"
```

---

## Why This Project Matters

This project demonstrates how AI can automate end-to-end content pipelines, reducing manual effort in research, writing, and distribution.

It reflects real-world applications in marketing automation, content operations, and AI-driven workflows.

---

## Key Learnings

- Designing modular AI pipelines
- Working with LLMs for structured generation
- Orchestrating multiple APIs in a workflow
- Building production-style automation systems

---

## Security Notes

- `.env` and API keys are excluded via `.gitignore`
- Gmail OAuth tokens stored locally (`token.json`)

---

## Future Improvements

- Web dashboard for workflow control
- Multi-recipient campaigns
- Scheduling and automation triggers
- Analytics and engagement tracking
- CRM integration

---

## Author

Asad
