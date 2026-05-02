"""RabbitMQ identifiers for email-service.

Email jobs use a durable work queue on the default exchange (routing key = queue
name), not a named fanout exchange like other OPD-Vertex services.
"""

from src.constants import DEFAULT_EMAIL_QUEUE_NAME

# Default durable queue name; also used as routing_key when publishing via default.
EMAIL_QUEUE = DEFAULT_EMAIL_QUEUE_NAME
