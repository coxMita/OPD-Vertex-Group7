import logging
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import KEYCLOAK_CERTS_URL

logger = logging.getLogger(__name__)

security = HTTPBearer()

_jwks_cache: dict[str, dict[str, Any] | None] = {"value": None}


async def get_jwks() -> dict:
    """Return the cached JWKS, fetching it from Keycloak when needed."""
    if _jwks_cache["value"] is None:
        try:
            logger.info("Fetching Keycloak JWKS from %s", KEYCLOAK_CERTS_URL)
            async with httpx.AsyncClient() as client:
                response = await client.get(KEYCLOAK_CERTS_URL, timeout=5.0)
                response.raise_for_status()
                _jwks_cache["value"] = response.json()
        except Exception as e:
            logger.error("Failed to fetch Keycloak JWKS: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not fetch authentication keys",
            ) from e
    return _jwks_cache["value"] or {}


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify the Keycloak JWT token."""
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
        jwks = await get_jwks()

        rsa_key = {}
        if "kid" not in unverified_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header["kid"]:
                rsa_key = key
                break

        if not rsa_key:
            # Force JWKS refresh
            _jwks_cache["value"] = None
            jwks = await get_jwks()
            for key in jwks.get("keys", []):
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = key
                    break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload

    except JWTError as e:
        logger.error("JWT verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
