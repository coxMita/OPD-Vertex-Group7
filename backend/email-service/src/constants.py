"""Process-wide defaults (no environment loading).

The API gateway only proxies HTTP; it does not supply broker or SMTP settings.
Those remain environment variables for this service's worker.
"""

DEFAULT_EMAIL_QUEUE_NAME = "email_queue"
