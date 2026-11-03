from trendmanu.utils import (
    display_topic,
    format_int,
    format_volume,
    normalize_text,
    same_topic,
    youtube_search_url,
)


def test_normalize_text_removes_accents_and_symbols():
    assert normalize_text("  Pensión   BIENESTAR, 2026! ") == "pension bienestar 2026"


def test_same_topic_allows_reasonable_containment():
    assert same_topic("Claudia Sheinbaum", "claudia sheinbaum")
    assert same_topic("sheinbaum", "Claudia Sheinbaum")
    assert not same_topic("ia", "inteligencia artificial")
    assert not same_topic("paris", "exposición de arte")


def test_display_topic_is_readable_but_preserves_brand_case():
    assert display_topic("claudia sheinbaum") == "Claudia Sheinbaum"
    assert display_topic("inteligencia artificial") == "Inteligencia Artificial"
    assert display_topic("ChatGPT") == "ChatGPT"


def test_format_volume_uses_latam_style():
    assert format_volume(0) == "—"
    assert format_volume(950) == "950"
    assert format_volume(12_400) == "12,4 mil"
    assert format_volume(2_400_000) == "2,4 M"


def test_format_int_uses_dots_as_thousands_separator():
    assert format_int(1234567) == "1.234.567"


def test_youtube_search_url_encodes_topic():
    url = youtube_search_url("inteligencia artificial")
    assert url.startswith("https://www.youtube.com/results?search_query=")
    assert "inteligencia+artificial" in url
