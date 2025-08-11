import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure every request has a correlation/request ID.

    - Reads from X-Request-ID if present; otherwise generates a UUID4.
    - Sets request.state.correlation_id and X-Request-ID response header.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.header_name)
        if not request_id:
            request_id = str(uuid.uuid4())
        request.state.correlation_id = request_id
        response: Response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response
