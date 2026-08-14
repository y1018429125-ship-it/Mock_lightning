"""Token generation and validation for the mock server.

Multi-account mode: three independent accounts (YFZX-1/2/3) each hold
their own token. Re-login of one account only overwrites that account's
token; the other accounts' tokens remain valid.
"""

import secrets

# account -> password
_ACCOUNTS: dict[str, int] = {
    "YFZX-1": 123456,
    "YFZX-2": 123456,
    "YFZX-3": 123456,
}

# account -> current valid token
_tokens: dict[str, str] = {}

# Most recently generated token (used as Swagger UI default value)
_latest_token: str | None = None


def login(account: str, password: int) -> str | None:
    """Validate credentials; on success generate/overwrite this account's
    token and return it. Return None if credentials do not match."""
    global _latest_token
    if _ACCOUNTS.get(account) != password:
        return None
    token = secrets.token_hex(128)
    _tokens[account] = token
    _latest_token = token
    return token


def validate_token(token: str) -> bool:
    """Check if the provided token is any account's current valid token."""
    return token in _tokens.values()


def get_token() -> str | None:
    """Return the most recently generated token, or None if nobody logged in."""
    return _latest_token
