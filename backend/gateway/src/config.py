"""Configuration for the API Gateway."""

import os

from dotenv import load_dotenv

load_dotenv()

APPOINTMENT_SERVICE_URL = os.getenv("APPOINTMENT_SERVICE_URL")
if not APPOINTMENT_SERVICE_URL:
    raise RuntimeError("APPOINTMENT_SERVICE_URL is not found.")

CONSULTATION_SERVICE_URL = os.getenv("CONSULTATION_SERVICE_URL")
if not CONSULTATION_SERVICE_URL:
    raise RuntimeError("CONSULTATION_SERVICE_URL is not found.")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL")
if not USER_SERVICE_URL:
    raise RuntimeError("USER_SERVICE_URL is not found.")

PRESCRIPTION_SERVICE_URL = os.getenv("PRESCRIPTION_SERVICE_URL")
if not PRESCRIPTION_SERVICE_URL:
    raise RuntimeError("PRESCRIPTION_SERVICE_URL is not found.")

TRANSCRIPTION_SERVICE_URL = os.getenv("TRANSCRIPTION_SERVICE_URL")
if not TRANSCRIPTION_SERVICE_URL:
    raise RuntimeError("TRANSCRIPTION_SERVICE_URL is not found.")

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")

KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "opd-vertex")
KEYCLOAK_EXTERNAL_URL = os.getenv("KEYCLOAK_EXTERNAL_URL", "http://localhost:8089")
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", KEYCLOAK_EXTERNAL_URL)
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "vue-app")
KEYCLOAK_CERTS_URL = (
    f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
)
