import logging
import os
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWKClient, PyJWKClientError

logger = logging.getLogger(__name__)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_EXTERNAL_URL = os.getenv("KEYCLOAK_EXTERNAL_URL", "http://localhost:8089")
REALM = os.getenv("KEYCLOAK_REALM", "opd-vertex")

JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"

jwks_client = PyJWKClient(JWKS_URL)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{KEYCLOAK_EXTERNAL_URL}/realms/{REALM}/protocol/openid-connect/token"
)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Validate the Keycloak token and return the payload."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except PyJWKClientError as e:
        logger.error("JWK client error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Keycloak public keys",
        ) from e
    except jwt.InvalidTokenError as e:
        logger.error("JWT Validation Error: %s", e)
        raise credentials_exception from e
