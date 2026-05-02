"""OTP request/response DTOs for email-service."""

from pydantic import BaseModel


class OtpSendRequest(BaseModel):
    """Request body for sending an OTP."""

    email: str


class OtpVerifyRequest(BaseModel):
    """Request body for verifying an OTP."""

    email: str
    code: str


class OtpVerifyResponse(BaseModel):
    """Response body for OTP verification."""

    valid: bool
