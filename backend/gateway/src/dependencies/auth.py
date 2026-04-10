"""JWT validation using Keycloak public keys."""

import logging
from functools import lru_cache

import httpx
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

KEYCLOAK_INTERNAL_URL = "http://keycloak:8180"  # pentru JWKS fetch
REALM = "opd-vertex"
JWKS_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/certs"
ISSUER = "http://localhost:8180/realms/opd-vertex"  # ce apare în token


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Fetch JWKS from Keycloak (cached)."""
    response = httpx.get(JWKS_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token against Keycloak public keys.

    Args:
        token: The raw JWT string.

    Returns:
        dict: The decoded token payload.

    Raises:
        HTTPException: 401 if token is invalid or expired.

    """
    try:
        jwks = _get_jwks()
        header = jwt.get_unverified_header(token)
        key = next(
            (k for k in jwks["keys"] if k["kid"] == header["kid"]),
            None,
        )
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: signing key not found",
            )
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=ISSUER,
            options={
                "verify_exp": True,
                "verify_aud": False,
            },
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        ) from e


def require_doctor(request: Request) -> dict:
    """Extract Bearer token from request and validate doctor role.

    Args:
        request: The incoming FastAPI request.

    Returns:
        dict: The decoded token payload.

    Raises:
        HTTPException: 401 if no/invalid token, 403 if missing doctor role.

    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)

    realm_roles: list[str] = payload.get("realm_access", {}).get("roles", [])
    if "doctor" not in realm_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor role required",
        )
    return payload
