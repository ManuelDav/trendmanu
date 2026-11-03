from trendmanu.trends import _parse_datetime, _parse_traffic, _to_float


def test_parse_traffic_accepts_plus_suffix():
    assert _parse_traffic("200+") == 200
    assert _parse_traffic("1.000+") == 1000
    assert _parse_traffic(None) == 0


def test_to_float_handles_breakout_and_percentages():
    assert _to_float("5,000") == 5000
    assert _to_float("250%") == 250
    assert _to_float("Breakout") == 5000
    assert _to_float(None) == 0


def test_parse_datetime_returns_aware_datetime():
    value = _parse_datetime("Tue, 3 Nov 2026 06:20:00 -0800")
    assert value is not None
    assert value.year == 2026
    assert value.tzinfo is not None
