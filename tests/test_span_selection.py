from datetime import date

from dei_extractor.logic.span_selection import Bill, select_year_span


def b(ps, pe):
    return Bill(True, ps, pe)


def test_happy_path_365():
    res = select_year_span(
        [
            b(date(2022, 12, 10), date(2023, 1, 10)),  # near start
            b(date(2023, 12, 20), date(2024, 1, 5)),  # near end
        ],
        year=2023,
        window_days=60,
        target_span_days=365,
    )
    assert res.start and res.end
    assert res.span_days is not None
    assert abs(res.span_days - 365) <= 5


def test_fallbacks_best_effort():
    res = select_year_span(
        [
            b(date(2022, 9, 1), date(2022, 10, 1)),  # far from start anchor
            b(date(2024, 3, 1), date(2024, 4, 1)),  # far from end anchor
        ],
        year=2023,
        window_days=60,
        target_span_days=365,
    )
    assert res.start or res.end


def test_no_settlements():
    # No settlement bills
    non_settlement = [
        Bill(False, date(2022, 12, 15), date(2023, 1, 15)),
        Bill(False, date(2023, 11, 15), date(2024, 1, 10)),
    ]
    res = select_year_span(non_settlement, year=2023)
    assert res.start is None and res.end is None and res.span_days is None


def test_tie_breakers():
    # Multiple candidates; ensure tie-breakers apply deterministically
    bills = [
        b(date(2022, 11, 25), date(2023, 1, 5)),  # start cand A (closer to anchor)
        b(date(2022, 12, 1), date(2023, 1, 12)),  # start cand B
        b(date(2023, 12, 20), date(2024, 1, 3)),  # end cand A (closer to anchor)
        b(date(2023, 12, 10), date(2024, 1, 15)),  # end cand B
    ]
    res = select_year_span(bills, year=2023, window_days=60, target_span_days=365)
    assert res.start and res.end
    # Prefer start closer to 2023-01-01
    assert res.start.period_start == date(2022, 11, 25)
