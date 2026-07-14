from app.auth.jwt import create_download_token, create_token, decode_token


def test_download_ticket_is_scoped_and_short_lived():
    token = create_download_token("user-1", "org-1", "project-1")
    payload = decode_token(token)

    assert payload["type"] == "download"
    assert payload["scope"] == "project:download"
    assert payload["org"] == "org-1"
    assert payload["project"] == "project-1"
    assert payload["exp"] - payload["iat"] == 120


def test_access_token_is_not_a_download_ticket():
    payload = decode_token(
        create_token("user-1", "access", extra={"org": "org-1"})
    )
    assert payload["type"] != "download"
    assert payload.get("scope") != "project:download"
