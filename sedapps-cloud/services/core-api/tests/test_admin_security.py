import pytest
from fastapi import HTTPException

from app.api.v1.admin import require_admin
from app.config import settings


def test_admin_endpoints_reject_an_invalid_secret():
    with pytest.raises(HTTPException) as error:
        require_admin("invalid")

    assert error.value.status_code == 403


def test_admin_endpoints_accept_the_configured_secret():
    expected = settings.SEDAPPS_ADMIN_SECRET or settings.INTERNAL_API_TOKEN

    assert require_admin(expected) is None
