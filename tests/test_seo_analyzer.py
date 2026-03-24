"""
Unit tests for services/seo_analyzer.py.

All checks operate on BeautifulSoup objects so there is no network I/O.
"""
import pytest
from bs4 import BeautifulSoup

from services.seo_analyzer import (
    _check_canonical,
    _check_headings,
    _check_images,
    _check_meta_description,
    _check_structured_data,
    _check_title,
    _compute_score,
    _word_overlap,
    _words,
)


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, 'html.parser')


# ---------------------------------------------------------------------------
# _words
# ---------------------------------------------------------------------------

def test_words_empty():
    assert _words('') == []

def test_words_single():
    assert _words('hello') == ['hello']

def test_words_multiple():
    assert _words('running shoes') == ['running', 'shoes']

def test_words_extra_whitespace():
    assert _words('  a  b  ') == ['a', 'b']


# ---------------------------------------------------------------------------
# _word_overlap
# ---------------------------------------------------------------------------

def test_word_overlap_identical():
    assert set(_word_overlap('running shoes', 'running shoes')) == {'running', 'shoes'}

def test_word_overlap_none():
    assert _word_overlap('cats', 'dogs') == []

def test_word_overlap_partial():
    result = _word_overlap('best running shoes', 'running')
    assert 'running' in result


# ---------------------------------------------------------------------------
# _check_title
# ---------------------------------------------------------------------------

def test_check_title_missing():
    hints = _check_title(soup('<html><body></body></html>'), 'shoes')
    assert len(hints) == 1
    assert hints[0].severity == 'critical'
    assert hints[0].category == 'title'

def test_check_title_good():
    hints = _check_title(soup('<title>Best running shoes</title>'), 'running shoes')
    assert hints == []

def test_check_title_too_long():
    long_title = 'A' * 61
    hints = _check_title(soup(f'<title>{long_title}</title>'), 'query')
    severities = {h.severity for h in hints}
    assert 'warning' in severities

def test_check_title_no_keywords():
    hints = _check_title(soup('<title>Welcome to my site</title>'), 'running shoes')
    assert any(h.severity == 'warning' for h in hints)


# ---------------------------------------------------------------------------
# _check_meta_description
# ---------------------------------------------------------------------------

def test_check_meta_description_missing():
    hints = _check_meta_description(soup('<html></html>'), 'shoes')
    assert len(hints) == 1
    assert hints[0].severity == 'critical'

def test_check_meta_description_good():
    html = '<meta name="description" content="Buy the best running shoes online.">'
    hints = _check_meta_description(soup(html), 'running shoes')
    assert hints == []

def test_check_meta_description_too_long():
    content = 'A' * 161
    html = f'<meta name="description" content="{content}">'
    hints = _check_meta_description(soup(html), 'query')
    assert any(h.severity == 'warning' for h in hints)

def test_check_meta_description_no_keywords():
    html = '<meta name="description" content="Welcome to our website.">'
    hints = _check_meta_description(soup(html), 'running shoes')
    assert any(h.severity == 'warning' for h in hints)


# ---------------------------------------------------------------------------
# _check_headings
# ---------------------------------------------------------------------------

def test_check_headings_single_h1_with_keywords():
    html = '<h1>Best running shoes</h1>'
    hints = _check_headings(soup(html), 'running shoes')
    assert not any(h.message in ('No H1 heading', 'Multiple H1 headings') for h in hints)

def test_check_headings_no_h1():
    html = '<h2>Some heading</h2>'
    hints = _check_headings(soup(html), 'running shoes')
    assert any(h.severity == 'critical' and 'No H1' in h.message for h in hints)

def test_check_headings_multiple_h1():
    html = '<h1>First</h1><h1>Second</h1>'
    hints = _check_headings(soup(html), 'query')
    assert any(h.severity == 'critical' and 'Multiple' in h.message for h in hints)

def test_check_headings_low_keyword_overlap():
    html = '<h1>Welcome</h1><h2>About us</h2>'
    hints = _check_headings(soup(html), 'running shoes')
    assert any(h.severity == 'warning' for h in hints)


# ---------------------------------------------------------------------------
# _check_images
# ---------------------------------------------------------------------------

def test_check_images_all_have_alt():
    html = '<img src="a.png" alt="A shoe"><img src="b.png" alt="Another shoe">'
    assert _check_images(soup(html)) == []

def test_check_images_missing_alt():
    html = '<img src="a.png"><img src="b.png" alt="ok">'
    hints = _check_images(soup(html))
    assert len(hints) == 1
    assert hints[0].severity == 'warning'
    assert '1 of 2' in hints[0].recommendation

def test_check_images_no_images():
    assert _check_images(soup('<p>No images here</p>')) == []


# ---------------------------------------------------------------------------
# _check_canonical
# ---------------------------------------------------------------------------

def test_check_canonical_present():
    html = '<link rel="canonical" href="https://example.com/">'
    assert _check_canonical(soup(html), 'https://example.com/') == []

def test_check_canonical_missing():
    hints = _check_canonical(soup('<html></html>'), 'https://example.com/')
    assert len(hints) == 1
    assert hints[0].severity == 'warning'
    assert hints[0].category == 'links'


# ---------------------------------------------------------------------------
# _check_structured_data
# ---------------------------------------------------------------------------

def test_check_structured_data_valid_json_ld():
    html = '<script type="application/ld+json">{"@type": "WebPage"}</script>'
    hints = _check_structured_data(soup(html))
    assert not any(h.severity == 'critical' for h in hints)

def test_check_structured_data_missing():
    hints = _check_structured_data(soup('<html></html>'))
    assert any(h.category == 'structured_data' and h.severity == 'info' for h in hints)

def test_check_structured_data_invalid_json_ld():
    html = '<script type="application/ld+json">{ invalid json }</script>'
    hints = _check_structured_data(soup(html))
    assert any(h.severity == 'critical' for h in hints)

def test_check_structured_data_microdata():
    html = '<div itemscope itemtype="https://schema.org/Product"><p>Item</p></div>'
    hints = _check_structured_data(soup(html))
    assert any('microdata' in h.message.lower() or 'JSON-LD' in h.message for h in hints)


# ---------------------------------------------------------------------------
# _compute_score
# ---------------------------------------------------------------------------

def test_compute_score_no_hints():
    assert _compute_score([]) == 100

def test_compute_score_one_critical():
    from models.seo import SEOHint
    hint = SEOHint(category='title', severity='critical', message='x', recommendation='y')
    assert _compute_score([hint]) == 80

def test_compute_score_one_warning():
    from models.seo import SEOHint
    hint = SEOHint(category='title', severity='warning', message='x', recommendation='y')
    assert _compute_score([hint]) == 90

def test_compute_score_one_info():
    from models.seo import SEOHint
    hint = SEOHint(category='title', severity='info', message='x', recommendation='y')
    assert _compute_score([hint]) == 98

def test_compute_score_floors_at_zero():
    from models.seo import SEOHint
    hints = [
        SEOHint(category='title', severity='critical', message='x', recommendation='y')
        for _ in range(10)
    ]
    assert _compute_score(hints) == 0
