from datetime import date
from threading import Lock

from fastapi import HTTPException, status

from app.core.config import get_daily_gemini_cap

_lock = Lock()
_counter_date: date | None = None
_counter = 0


def check_and_increment_daily_gemini_cap() -> None:
    """In-memory, single-process daily soft cap on /execute calls, shared
    across *all* users. Gemini's free tier only allows a small number of
    requests per day (currently 20, tracked per model) — without this,
    real traffic on a deployed instance would exhaust it in minutes and
    every subsequent user would see a raw, confusing 502 from Gemini.
    This fails fast instead, with a clear message.

    Resets at local midnight. Not multi-worker safe — fine for a single
    Render free-tier instance; move the counter to Redis/DB if you scale
    to multiple workers.
    """
    global _counter_date, _counter
    cap = get_daily_gemini_cap()
    today = date.today()

    with _lock:
        if _counter_date != today:
            _counter_date = today
            _counter = 0

        if _counter >= cap:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Günlük ücretsiz kullanım kotası doldu ({cap} istek). "
                    "Lütfen yarın tekrar deneyin."
                ),
            )

        _counter += 1
