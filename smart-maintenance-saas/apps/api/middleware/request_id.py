import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response

from core.logging_config import correlation_id_var  # Import the context variable


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure every request has a correlation/request ID.

    - Reads from X-Request-ID if present; otherwise generates a UUID4.
    - Sets request.state.correlation_id and X-Request-ID response header.
    - Sets the correlation_id context variable for logging.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.header_name)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Set the context variable for logging
        correlation_id_var.set(request_id)
        request.state.correlation_id = request_id
        
        response: Response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response
