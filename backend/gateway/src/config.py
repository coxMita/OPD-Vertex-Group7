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
