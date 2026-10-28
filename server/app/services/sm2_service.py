"""
sm2_service.py — SuperMemo SM-2 Spaced Repetition calculation service.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict


def calculate_sm2_metrics(
    review_rating: int,
    prev_ef: float = 2.5,
    prev_interval: int = 1,
    prev_repetitions: int = 0,
) -> Dict[str, Any]:
    """
    Thuật toán SuperMemo SM-2 chuẩn hóa cho thang điểm 1-4.
    Map [1, 2, 3, 4] -> thang SuperMemo q trong [2, 3, 4, 5].
    Returns dict containing ease_factor, interval_days, repetitions, and next_review_date.
    """
    q_sm = review_rating + 1
    new_ef = prev_ef + (0.1 - (5 - q_sm) * (0.08 + (5 - q_sm) * 0.02))
    if new_ef < 1.3:
        new_ef = 1.3

    if review_rating < 3:
        # Đánh giá 1 (Again/Quên) hoặc 2 (Hard/Khó chưa đạt) -> lặp lại từ đầu
        new_repetitions = 0
        new_interval = 1
    else:
        # Đánh giá 3 (Good/Tốt) hoặc 4 (Easy/Dễ dàng) -> tăng chu kỳ
        new_repetitions = prev_repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = max(1, round(prev_interval * new_ef))
        if review_rating == 4:
            new_interval = round(new_interval * 1.3)

    now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
    next_review_date = now_dt + timedelta(days=new_interval)

    return {
        "ease_factor": round(new_ef, 2),
        "interval_days": new_interval,
        "repetitions": new_repetitions,
        "next_review_date": next_review_date,
        "reviewed_at": now_dt,
    }

