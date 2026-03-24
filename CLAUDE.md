# SEO Demo

A FastAPI web app that fetches a URL, runs on-page SEO checks against a user-supplied search query, and returns actionable hints with a score.

## Running the app

```bash
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

Open http://localhost:8000.

## Project structure

```
main.py               # FastAPI app, mounts static files and templates
requirements.txt      # Pinned dependencies
models/seo.py         # Pydantic request/response models (AnalyzeRequest, AnalyzeResponse, SEOHint)
routers/seo.py        # POST /api/seo/analyze endpoint
services/seo_analyzer.py  # Core analysis logic and Playwright screenshot
templates/index.html  # Jinja2 frontend template
static/css/style.css
static/js/app.js
```

## Architecture

- The browser submits a JSON POST to `/api/seo/analyze`.
- `seo_analyzer.analyze()` fetches the page with `httpx`, parses the HTML once with BeautifulSoup, and runs all checks concurrently with `get_page_image()` via `asyncio.gather`.
- `get_page_image()` launches a headless Chromium browser via Playwright, navigates to the URL, and returns a base64-encoded PNG screenshot.
- Results are rendered client-side in `app.js` — no page reload.

## Adding a new SEO check

1. Add a `_check_<name>(soup, ...)` function in `services/seo_analyzer.py` that returns `list[SEOHint]`.
2. Call it inside `_run_checks()` in `analyze()`.
3. If the check needs a new `category` value, add it to the `Literal` in `models/seo.py`.

## Virtual environment

The venv lives in `seodemo/` and is excluded from version control via `.gitignore`.
