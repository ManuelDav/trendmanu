from trendmanu.models import Candidate, YouTubeMetrics
from trendmanu.scoring import (
    competition_score,
    label_for,
    rank_candidates,
    score_candidate,
    source_label,
    traction_score,
)


def make_candidate(
    topic="inteligencia artificial",
    signals=None,
    traffic=1_000,
    growth=0.0,
    weekly_interest=0.0,
    weekly_growth=0.0,
    views=0,
    total_results=0,
    sources=None,
    context="",
):
    return Candidate(
        topic=topic,
        key=topic,
        sources={"google"} if sources is None else sources,
        signals={"rising"} if signals is None else set(signals),
        traffic=traffic,
        growth=growth,
        weekly_interest=weekly_interest,
        weekly_growth=weekly_growth,
        context=context,
        youtube=YouTubeMetrics(
            available=True,
            videos_found=min(total_results, 25),
            total_results=total_results,
            views_7d=views,
        ),
    )


def test_label_thresholds():
    assert label_for(100)[1] == "high"
    assert label_for(80)[1] == "high"
    assert label_for(79)[1] == "good"
    assert label_for(60)[1] == "good"
    assert label_for(59)[1] == "watch"
    assert label_for(40)[1] == "watch"
    assert label_for(39)[1] == "low"
    assert label_for(0)[1] == "low"


def test_rising_gets_more_search_weight_than_daily():
    rising = make_candidate(signals={"rising"}, growth=500, traffic=1_000)
    daily = make_candidate(signals={"daily"}, traffic=1_000)
    rising_score = score_candidate(rising, ["tecnología"])
    daily_score = score_candidate(daily, ["tecnología"])
    assert rising_score.search_score > daily_score.search_score
    assert rising_score.score > daily_score.score


def test_more_views_improve_traction_and_score():
    low = make_candidate(views=5_000, total_results=100)
    high = make_candidate(views=2_000_000, total_results=100)
    assert traction_score(high) > traction_score(low)
    assert score_candidate(high, ["tecnología"]).score > score_candidate(low, ["tecnología"]).score


def test_less_competition_improves_competition_score():
    crowded = make_candidate(total_results=90_000)
    empty = make_candidate(total_results=3)
    assert competition_score(empty) > competition_score(crowded)


def test_affinity_rewards_matching_category():
    finance = make_candidate(topic="bitcoin y dolar", context="inversión y finanzas")
    unrelated = make_candidate(topic="novak djokovic", context="tenis")
    finance_score = score_candidate(finance, ["finanzas"])
    unrelated_score = score_candidate(unrelated, ["finanzas"])
    assert finance_score.affinity_category == "finanzas"
    assert finance_score.affinity_score > unrelated_score.affinity_score


def test_no_selected_categories_is_neutral():
    candidate = make_candidate()
    result = score_candidate(candidate, [])
    assert result.affinity_score == 50.0
    assert result.affinity_category == "Sin filtro"


def test_score_uses_declared_weights():
    candidate = make_candidate(
        signals={"rising"},
        growth=1_000,
        traffic=2_000,
        views=500_000,
        total_results=2_000,
        context="inteligencia artificial",
    )
    result = score_candidate(candidate, ["tecnología"])
    expected = round(
        0.40 * result.search_score
        + 0.30 * result.traction_score
        + 0.20 * result.competition_score
        + 0.10 * result.affinity_score
    )
    assert result.score == expected


def test_rank_filters_excluded_terms_and_orders_by_score():
    candidates = [
        make_candidate(topic="tema viral", signals={"rising"}, growth=5_000, views=1_000_000),
        make_candidate(topic="tema excluido", signals={"rising"}, growth=9_000, views=9_000_000),
        make_candidate(topic="tema normal", signals={"daily"}, traffic=100),
    ]
    ranked = rank_candidates(candidates, ["entretenimiento"], excluded_terms=["excluido"])
    assert [item.candidate.topic for item in ranked] == ["tema viral", "tema normal"]
    assert ranked[0].score >= ranked[1].score


def test_rank_limits_to_ten():
    candidates = [
        make_candidate(topic=f"tema {index}", signals={"daily"}, traffic=100 + index)
        for index in range(20)
    ]
    assert len(rank_candidates(candidates, [])) == 10


def test_source_label():
    assert source_label(make_candidate(sources={"google"})) == "Google"
    assert source_label(make_candidate(sources={"youtube"})) == "YouTube"
    assert source_label(make_candidate(sources={"google", "youtube"})) == "Ambas"
