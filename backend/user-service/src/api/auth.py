import logging
import os
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

security = HTTPBearer()

_jwks_cache: dict[str, dict[str, Any] | None] = {"value": None}
_keycloak_certs_url_cache: dict[str, str | None] = {"value": None}


def get_certs_url() -> str:
    """Return the Keycloak certs URL derived from the current environment."""
    if not _keycloak_certs_url_cache["value"]:
        realm = os.getenv("KEYCLOAK_REALM", "opd-vertex")
        external_url = os.getenv("KEYCLOAK_EXTERNAL_URL", "http://localhost:8089")
        _keycloak_certs_url_cache["value"] = (
            f"{external_url}/realms/{realm}/protocol/openid-connect/certs"
        )
    return _keycloak_certs_url_cache["value"] or ""


async def get_jwks() -> dict:
    """Return the cached JWKS, fetching it from Keycloak when needed."""
    if _jwks_cache["value"] is None:
        certs_url = get_certs_url()
        try:
            logger.info("Fetching Keycloak JWKS from %s", certs_url)
            async with httpx.AsyncClient() as client:
                response = await client.get(certs_url, timeout=5.0)
                response.raise_for_status()
                _jwks_cache["value"] = response.json()
        except Exception as e:
            logger.error("Failed to fetch Keycloak JWKS: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not fetch authentication keys",
            ) from e
    return _jwks_cache["value"] or {}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify the Keycloak JWT token and return the parsed payload."""
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
