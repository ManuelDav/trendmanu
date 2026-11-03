from trendmanu.models import Candidate, TrendSignal
from trendmanu.pipeline import (
    _merge_google_signals,
    _merge_youtube_topics,
    _select_for_youtube,
)
from trendmanu.youtube import YouTubeTopic


def test_merge_google_signals_combines_same_topic():
    signals = [
        TrendSignal("Pensión Bienestar", "daily", traffic=1_000, weekly_interest=45, weekly_growth=20),
        TrendSignal("pension bienestar", "rising", traffic=1_000, growth=500),
    ]
    merged = _merge_google_signals(signals)
    assert len(merged) == 1
    candidate = merged[0]
    assert candidate.signals == {"daily", "rising", "weekly"}
    assert candidate.growth == 500
    assert candidate.traffic == 1_000


def test_merge_youtube_topics_marks_source_and_adds_new_topics():
    candidates = [
        Candidate(
            topic="Claudia Sheinbaum",
            key="claudia sheinbaum",
            sources={"google"},
            signals={"daily"},
        )
    ]
    added = _merge_youtube_topics(
        candidates,
        [YouTubeTopic("sheinbaum", 3), YouTubeTopic("fútbol", 2)],
    )
    assert added == 1
    assert candidates[0].sources == {"google", "youtube"}
    assert any(candidate.topic == "fútbol" and candidate.sources == {"youtube"} for candidate in candidates)


def test_select_for_youtube_guarantees_youtube_only_topics():
    candidates = [
        Candidate(
            topic=f"tema google {index}",
            key=f"tema google {index}",
            sources={"google"},
            signals={"daily"},
            traffic=1_000,
        )
        for index in range(20)
    ]
    candidates.append(
        Candidate(
            topic="tema youtube",
            key="tema youtube",
            sources={"youtube"},
            signals={"youtube"},
        )
    )
    selected = _select_for_youtube(candidates, 15)
    assert len(selected) == 15
    assert any(candidate.key == "tema youtube" for candidate in selected)
