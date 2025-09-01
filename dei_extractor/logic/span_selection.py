from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class Bill:
    is_settlement: bool
    period_start: date
    period_end: date
    row_index: Optional[int] = None


@dataclass(frozen=True)
class SpanResult:
    start: Optional[Bill]
    end: Optional[Bill]
    span_days: Optional[int]
    notes: List[str]


def _nearest(
    bills: List[Bill], anchor: date, key_attr: str, max_days: int
) -> Optional[Bill]:
    # key_attr is "period_start" or "period_end"
    cand: List[Tuple[int, date, Bill]] = []
    for b in bills:
        d: date = getattr(b, key_attr)
        diff = abs((d - anchor).days)
        cand.append((diff, d, b))
    if not cand:
        return None
    cand.sort(key=lambda x: (x[0], x[1]))
    best = cand[0]
    return best[2] if best[0] <= max_days else None


def select_year_span(
    bills: Iterable[Bill],
    year: int = 2023,
    window_days: int = 60,
    target_span_days: int = 365,
    fallback_extra_days: int = 60,  # allows up to ±120 total if needed
) -> SpanResult:
    notes: List[str] = []
    bills = [b for b in bills if b.is_settlement]
    if not bills:
        return SpanResult(None, None, None, notes + ["No settlement bills."])

    anchor_start = date(year, 1, 1)
    anchor_end = date(year, 12, 31)

    win = timedelta(days=window_days)
    start_lo, start_hi = anchor_start - win, anchor_start + win
    end_lo, end_hi = anchor_end - win, anchor_end + win

    start_candidates = [b for b in bills if start_lo <= b.period_start <= start_hi]
    end_candidates = [b for b in bills if end_lo <= b.period_end <= end_hi]

    # Fallbacks if needed
    if not start_candidates:
        notes.append(
            "No start candidates in ±window; using nearest within ±(window+fallback)."
        )
        start_near = _nearest(
            bills, anchor_start, "period_start", window_days + fallback_extra_days
        )
        start_candidates = [start_near] if start_near else []

    if not end_candidates:
        notes.append(
            "No end candidates in ±window; using nearest within ±(window+fallback)."
        )
        end_near = _nearest(
            bills, anchor_end, "period_end", window_days + fallback_extra_days
        )
        end_candidates = [end_near] if end_near else []

    # If still empty on either side, return partial info
    if not start_candidates or not end_candidates:
        s = start_candidates[0] if start_candidates else None
        e = end_candidates[0] if end_candidates else None
        span = (
            (e.period_end - s.period_start).days + 1
            if (s and e and e.period_end >= s.period_start)
            else None
        )
        return SpanResult(
            s, e, span, notes + ["Incomplete candidates; returned best-effort."]
        )

    # Pair and score
    pairs: List[Tuple[Tuple[int, int, int, int], int, Bill, Bill]] = []
    for s in start_candidates:
        for e in end_candidates:
            if e.period_end >= s.period_start:
                span_days = (e.period_end - s.period_start).days + 1
                score = (
                    abs(span_days - target_span_days),
                    abs((s.period_start - anchor_start).days),
                    abs((e.period_end - anchor_end).days),
                    -span_days,  # prefer larger span if still tied
                )
                pairs.append((score, span_days, s, e))

    if not pairs:
        # No chronological pair found; pick nearests anyway
        s = (
            _nearest(start_candidates, anchor_start, "period_start", 10**9)
            or start_candidates[0]
        )
        e = (
            _nearest(end_candidates, anchor_end, "period_end", 10**9)
            or end_candidates[0]
        )
        span = (
            (e.period_end - s.period_start).days + 1
            if e.period_end >= s.period_start
            else None
        )
        notes.append("No valid (s<=e) pairs; returned nearests by anchors.")
        return SpanResult(s, e, span, notes)

    pairs.sort(key=lambda x: x[0])
    _, span_days, s, e = pairs[0]
    return SpanResult(s, e, span_days, notes)
