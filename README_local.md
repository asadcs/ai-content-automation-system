# AI Content Automation System -- Newsletter Workflow

An end-to-end AI-powered pipeline that researches topics, generates
structured HTML newsletters using Claude, creates AI infographics, and
delivers emails via Gmail API.

------------------------------------------------------------------------

## Overview

This project automates the full lifecycle of newsletter creation:

-   Researches topics using Perplexity API\
-   Generates structured, readable HTML content using Claude\
-   Creates AI-powered infographics (KIE AI / NanoBanan / Pillow
    fallback)\
-   Renders branded newsletters (Xerxes.AI style)\
-   Sends emails via Gmail API (draft + send modes)

Designed as a modular AI content pipeline with workflow orchestration,
extensible to other content formats.

------------------------------------------------------------------------

## Tech Stack

-   Python\
-   Claude (LLM for content generation)\
-   Perplexity API (research)\
-   Gmail API (email delivery)\
-   Jinja2 + Premailer (HTML rendering)\
-   Pillow / AI APIs (infographics)\
-   BeautifulSoup (HTML processing)

------------------------------------------------------------------------

## System Architecture

User Input → Research → Content Planning → Infographic Generation → HTML
Rendering → Email Delivery

------------------------------------------------------------------------

## Features

-   Automated topic research and summarization\
-   Structured multi-section newsletter generation\
-   AI-generated infographics with fallback support\
-   Readability optimization (grade ≤ 12)\
-   Branded HTML email rendering\
-   Gmail draft-first safety workflow\
-   Modular and extensible pipeline

------------------------------------------------------------------------

## Setup

### 1. Clone the repository

git clone
https://github.com/YOUR_USERNAME/ai-content-automation-system.git\
cd ai-content-automation-system

### 2. Install dependencies

pip install -r requirements.txt

### 3. Configure environment variables

Create a `.env` file:

PERPLEXITY_API_KEY=your_key\
GMAIL_SENDER_ADDRESS=your_email\
GMAIL_RECIPIENT_ADDRESS=recipient_email

### 4. Add Google credentials

-   Place `credentials.json` in the root directory\
-   Enable Gmail API in Google Cloud Console

------------------------------------------------------------------------

## Usage

### Step 1: Research Topic

python tools/research_topic.py --topic "AI agents" --audience "tech
professionals"

### Step 2: Generate Infographics

python tools/generate_infographics.py --prompts-json
.tmp/image_prompts.json

### Step 3: Generate Newsletter HTML

python tools/generate_newsletter_html.py --content .tmp/content.json
--images-dir .tmp/

### Step 4: Preview Newsletter

python tools/preview_newsletter.py --file .tmp/newsletter.html

### Step 5: Send via Gmail

python tools/send_gmail.py --html-file .tmp/newsletter.html --subject
"Your Subject"

------------------------------------------------------------------------

## Security Notes

-   `.env` and API keys are excluded via `.gitignore`\
-   Gmail OAuth tokens stored locally (`token.json`)

------------------------------------------------------------------------

## Future Improvements

-   Web dashboard for workflow control\
-   Multi-recipient email campaigns\
-   Scheduling and automation triggers\
-   Analytics and engagement tracking\
-   Integration with CRM tools

------------------------------------------------------------------------

## Author

Your Name
