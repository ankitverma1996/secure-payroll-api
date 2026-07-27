"""
Simplified OAuth2 client-credentials flow.

In production this would validate against a real identity provider
(Azure AD / MSAL, Auth0, etc.) and cache tokens with their real TTL.
This demo implements the same shape -- client authenticates once with
a client_id/client_secret, receives a short-lived bearer token, and
every subsequent request presents that token -- using an in-memory
store so the whole thing is runnable with no external dependencies.
"""

import secrets
import time
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

TOKEN_TTL_SECONDS = 300

# demo-only "registered clients" store: client_id -> client_secret
_REGISTERED_CLIENTS: Dict[str, str] = {
    "demo-client": "demo-secret",
}

# issued token -> expiry epoch
_ACTIVE_TOKENS: Dict[str, float] = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def issue_token(client_id: str, client_secret: str) -> str:
    expected = _REGISTERED_CLIENTS.get(client_id)
    if expected is None or expected != client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
        )

    token = secrets.token_urlsafe(32)
    _ACTIVE_TOKENS[token] = time.time() + TOKEN_TTL_SECONDS
    return token


def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    expiry = _ACTIVE_TOKENS.get(token)
    if expiry is None or expiry < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token
