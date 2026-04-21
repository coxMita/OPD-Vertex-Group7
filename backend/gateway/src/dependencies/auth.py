import logging
import httpx

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from src.config import KEYCLOAK_CERTS_URL, KEYCLOAK_CLIENT_ID

logger = logging.getLogger(__name__)

security = HTTPBearer()

_jwks = None

async def get_jwks() -> dict:
    global _jwks
    if _jwks is None:
        try:
            logger.info("Fetching Keycloak JWKS from %s", KEYCLOAK_CERTS_URL)
            async with httpx.AsyncClient() as client:
                response = await client.get(KEYCLOAK_CERTS_URL, timeout=5.0)
                response.raise_for_status()
                _jwks = response.json()
        except Exception as e:
            logger.error("Failed to fetch Keycloak JWKS: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not fetch authentication keys",
            )
    return _jwks

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verifies the Keycloak JWT token."""
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
            global _jwks
            _jwks = None
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
        )
