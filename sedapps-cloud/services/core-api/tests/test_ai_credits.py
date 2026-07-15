from datetime import datetime, timezone

import pytest

from app.models.ai_job import AiJob
from app.models.organization import Organization
from app.services.credits import (
    TOKENS_PER_CREDIT,
    _reset_if_due,
    credits_for_tokens,
    settle_job_credits,
)


@pytest.mark.parametrize(
    ("tokens", "credits"),
    [
        (-1, 0),
        (0, 0),
        (1, 1),
        (999, 1),
        (TOKENS_PER_CREDIT, 1),
        (TOKENS_PER_CREDIT + 1, 2),
        (2 * TOKENS_PER_CREDIT, 2),
    ],
)
def test_one_credit_represents_one_thousand_tokens(tokens: int, credits: int):
    assert credits_for_tokens(tokens) == credits


def test_monthly_reset_clears_used_and_reserved_credits():
    organization = Organization(
        name="Test",
        plan="free",
        ai_credits_used=42,
        ai_credits_reserved=8,
        ai_credits_reset_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )

    changed = _reset_if_due(
        organization, datetime(2026, 7, 15, tzinfo=timezone.utc)
    )

    assert changed is True
    assert organization.ai_credits_used == 0
    assert organization.ai_credits_reserved == 0
    assert organization.ai_credits_reset_at == datetime(
        2026, 8, 1, tzinfo=timezone.utc
    )


def test_settled_job_is_not_charged_twice():
    job = AiJob(credits_settled=True, charged_credits=7)

    assert settle_job_credits(None, job) == 7  # type: ignore[arg-type]
