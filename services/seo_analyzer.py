"""
SEO analysis service.

Fetch the target URL and evaluate common on-page SEO signals relative to the
supplied search query.  Each check returns one or more SEOHint objects; the
final score is a simple weighted roll-up.
"""

import asyncio
import base64
import json
import logging

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from models.seo import AnalyzeResponse, CompetitorResult, SEOHint
from services.ai import compute_similarity, compute_relevance_score
from services.llm import explain_relevance, search

logger = logging.getLogger(__name__)


async def analyze(url: str, search_query: str) -> AnalyzeResponse:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        response = await client.get(url)

    response.raise_for_status()
    html = response.text

    async def _run_checks() -> tuple[list[SEOHint], int, float | None, float | None]:
        soup = BeautifulSoup(html, 'html.parser')
        hints: list[SEOHint] = []
        hints += _check_title(soup, search_query)
        hints += _check_meta_description(soup, search_query)
        hints += _check_headings(soup, search_query)
        hints += _check_images(soup)
        hints += _check_canonical(soup, url)
        hints += _check_structured_data(soup)
        page_text = soup.get_text()
        similarity, rel_score = await asyncio.gather(
            asyncio.to_thread(compute_similarity, page_text, search_query),
            asyncio.to_thread(compute_relevance_score, page_text, search_query),
        )
        return hints, _compute_score(hints), similarity, rel_score

    (hints, score, semantic_similarity, relevance_score), page_image, competitor_dicts = (
        await asyncio.gather(
            _run_checks(),
            get_page_image(url),
            search(search_query),
        )
    )

    competition_summary = await explain_relevance(
        query=search_query,
        url=url,
        search_results=competitor_dicts,
    )

    return AnalyzeResponse(
        url=url,
        search_query=search_query,
        score=score,
        hints=hints,
        page_image=page_image,
        semantic_similarity=semantic_similarity,
        relevance_score=relevance_score,
        competitors=[CompetitorResult(**r) for r in competitor_dicts],
        competition_summary=competition_summary,
    )


async def get_page_image(url: str) -> str | None:
    """Navigate to *url* with a headless browser and return a base64-encoded PNG screenshot."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            await page.goto(url, wait_until="load", timeout=30000)
            screenshot_bytes = await page.screenshot(full_page=False)
            await browser.close()
        return base64.b64encode(screenshot_bytes).decode()
    except Exception as exc:
        logger.warning("get_page_image failed for %s: %s", url, exc)
        return None


def _words(s: str) -> list[str]:
    """Returns a list of words found in the string."""
    return [word for word in s.strip().split(' ') if len(word.strip()) > 0]


def _word_overlap(s: str, t: str) -> list[str]:
    """Returns the number of words that exist in both strings."""
    s_words = _words(s)
    t_words = _words(t)
    overlap = set(t_words).intersection(s_words)
    return list(overlap)


# ---------------------------------------------------------------------------
# Individual checks — each returns a (possibly empty) list of SEOHint objects.
# ---------------------------------------------------------------------------

def _check_title(soup: BeautifulSoup, query: str) -> list[SEOHint]:
    """Check that a <title> tag exists, is an appropriate length, and contains
    keywords from the search query."""
    title = soup.title or None
    hints = list()
    if not title:
        hints.append(SEOHint(
            category='title',
            severity='critical',
            message='No title was found.',
            recommendation='Ensure the <title> tag exists, is 50–60 characters, and contains the target keyword.',
        ))
    else:
        title_text = title.string
        if len(title_text.strip()) > 60:
            hints.append(SEOHint(
                category='title',
                severity='warning',
                message="The page title is a little long",
                recommendation=f'The title has {len(title_text)} characters, try to use 50-60 characters if possible.'
            ))
        overlap = _word_overlap(title_text, query)
        if len(overlap) == 0:
            hints.append(SEOHint(
                category='title',
                severity='warning',
                message="The page title doesn't contain any of the search terms",
                recommendation='Try to include some or all of the words in the query in the page title.'
            ))
    return hints

def _check_meta_description(soup: BeautifulSoup, query: str) -> list[SEOHint]:
    """Check that a meta description exists and is an appropriate length."""
    tag = soup.find("meta", attrs={"name": "description"})
    description = tag["content"] if tag else None
    hints = list()
    if not tag:
        hints.append(SEOHint(
            category='meta',
            severity='critical',
            message='No meta description was found.',
            recommendation="Add a unique meta description of 150–160 characters containing the target keyword.",
        ))
    else:
        if len(description.strip()) > 160:
            hints.append(SEOHint(
                category='meta',
                severity='warning',
                message='The meta description is a bit long',
                recommendation=f"The meta description has {len(description)} characters, try to use 150-160 characters if possible."
            ))
        overlap = _word_overlap(description, query)
        if len(overlap) == 0:
            hints.append(SEOHint(
                category='meta',
                severity='warning',
                message='The meta description does not contain any of the search terms.',
                recommendation="Try to include some or all of the words in the query in the meta description."
            ))
    return hints


def _check_headings(soup: BeautifulSoup, query: str) -> list[SEOHint]:
    """Check for a single H1, keyword presence in headings, and heading hierarchy."""
    # TODO: implement
    h1s = soup.find_all("h1")
    hints = list()
    if len(h1s) == 0:
        hints.append(SEOHint(
            category='headings',
            severity='critical',
            message='No H1 heading',
            recommendation="Try to include a single H1 heading"
        ))
    elif len(h1s) > 1:
        hints.append(SEOHint(
            category='headings',
            severity='critical',
            message='Multiple H1 headings',
            recommendation="Try to include a single H1 heading"
        ))
    # Compute an average overlap score of some description
    overlaps = list()
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    for tag in headings:
        overlap = _word_overlap(tag.get_text(strip=True), query)
        overlaps.append(len(overlap))
    if not overlaps:
        return hints
    avg_overlap = sum(overlaps) / len(overlaps)
    if avg_overlap < 1:
        hints.append(SEOHint(
            category='headings',
            severity='warning',
            message="Low number of search terms in headings",
            recommendation=f"An average of {avg_overlap:.2f} search terms per heading was found.  Bumping this up can improve your site's relevancy to the search."
        ))
    return hints


def _check_images(soup: BeautifulSoup) -> list[SEOHint]:
    """Check that all <img> tags have descriptive alt attributes."""
    imgs = soup.find_all("img")
    missing_alt = [img for img in imgs if not img.get("alt")]
    hints = list()
    if len(missing_alt) > 0:
        hints.append(SEOHint(
            category='links',
            severity='warning',
            message="One or more images are missing ALT text",
            recommendation=f"{len(missing_alt)} of {len(imgs)} images are missing ALT text."
        ))
    return hints


def _check_canonical(soup: BeautifulSoup, url: str) -> list[SEOHint]:
    """Check for a canonical link tag."""
    hints = list()
    canonical = soup.find("link", attrs={"rel": "canonical"})
    url = canonical["href"] if canonical else None
    if not url:
        hints.append(SEOHint(
            category='links',
            severity='warning',
            message='No canonical link tag found.',
            recommendation=(
                'A canonical link tag tells search engines which URL is the "official" version of a page '
                'when the same (or very similar) content is accessible at multiple URLs.  Without it, a search engine '
                'may see these as duplicate content and split ranking signals across them, weakening all of them.'
            ),
        ))
    return hints


def _check_structured_data(soup: BeautifulSoup) -> list[SEOHint]:
    """Check for JSON-LD or microdata structured data markup."""
    hints = list()
    tag = soup.find("script", attrs={"type": "application/ld+json"})
    try:
        json_ld_data = json.loads(tag.string) if tag else None
        if not json_ld_data:
            hints.append(SEOHint(
                category='structured_data',
                severity='info',
                message='No JSON-LD found',
                recommendation='Consider adding structured data to the page - it can help search engines understand your content'
            ))
    except json.JSONDecodeError:
        hints.append(SEOHint(
            category='structured_data',
            severity='critical',
            message='Possibly invalid JSON-LD',
            recommendation='Failed to parse the JSON-LD payload, double-check to ensure validity'
        ))
    has_microdata = bool(soup.find(attrs={"itemscope": True}))
    if has_microdata:
        hints.append(SEOHint(
            category='structured_data',
            severity='info',
            message='Consider switching to JSON-LD',
            recommendation=(
                "Consider replacing the microdata with JSON-LD: it's easier to maintain "
                "since it's separate from the HTML structure, and it's "
                "simpler to parse programmatically."
            )
        ))
    return hints


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

_SEVERITY_PENALTY = {"critical": 20, "warning": 10, "info": 2}


def _compute_score(hints: list[SEOHint]) -> int:
    penalty = sum(_SEVERITY_PENALTY.get(h.severity, 0) for h in hints)
    return max(0, 100 - penalty)
