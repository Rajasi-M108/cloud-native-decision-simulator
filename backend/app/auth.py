"""
Auth layer — verifies Cognito-issued JWTs in production.

Locally (no COGNITO_* env vars set), auth is bypassed so the API is usable
without standing up Cognito first. In production, set:
  COGNITO_REGION, COGNITO_USERPOOL_ID, COGNITO_APP_CLIENT_ID
and every request must carry a valid Bearer token.
"""
import os
from functools import lru_cache

import requests
from fastapi import Depends, HTTPException, Request
from jose import jwt

COGNITO_REGION = os.getenv("COGNITO_REGION")
USERPOOL_ID = os.getenv("COGNITO_USERPOOL_ID")
APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")

AUTH_ENABLED = bool(COGNITO_REGION and USERPOOL_ID and APP_CLIENT_ID)


@lru_cache
def _jwks():
    url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USERPOOL_ID}/.well-known/jwks.json"
    return requests.get(url, timeout=5).json()


def _dev_user():
    return {"sub": "dev-user", "role": "manager", "email": "dev@example.com"}


def get_current_user(request: Request) -> dict:
    if not AUTH_ENABLED:
        return _dev_user()

    authz = request.headers.get("Authorization", "")
    if not authz.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authz.split(" ", 1)[1]

    try:
        headers = jwt.get_unverified_headers(token)
        key = next(k for k in _jwks()["keys"] if k["kid"] == headers["kid"])
        claims = jwt.decode(token, key, algorithms=["RS256"], audience=APP_CLIENT_ID)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    return {
        "sub": claims.get("sub"),
        "role": claims.get("custom:role", "manager"),
        "email": claims.get("email"),
    }


def require_role(*roles):
    def checker(user: dict = Depends(get_current_user)):
        if roles and user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return checker
