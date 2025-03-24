import logging
from apps.logs.utils import log_message


class RequestLoggingMiddleware:
    """Middleware to log all incoming requests and responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/'):
            log_message(request.path,logging.INFO, f"Request: {request.method} {request.path}", request)
            log_message(request.path,logging.INFO, f"Response: {response.status_code} {request.path}", request)
        return response