import logging
import uuid

logger = logging.getLogger(__name__)


class RequestCorrelationMiddleware:
    """
    Middleware that attaches a unique X-Request-ID header to all incoming requests
    and injects it into response headers and logging context.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = request_id

        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
