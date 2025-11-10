from schemas.google_dto import GoogleAuthResponse, GoogleCallbackResponse, GoogleErrorResponse


def test_google_auth_response():
    resp = GoogleAuthResponse(authorization_url="https://accounts.google.com/...")
    assert resp.authorization_url.startswith("https://")


def test_google_callback_response():
    resp = GoogleCallbackResponse(redirect_url="http://localhost:3000/callback?token=abc")
    assert "token" in resp.redirect_url


def test_google_error_response():
    err = GoogleErrorResponse(error="Invalid code")
    assert err.error == "Invalid code"
    assert err.details is None

    err = GoogleErrorResponse(error="Token expired", details="Try again")
    assert err.details == "Try again"