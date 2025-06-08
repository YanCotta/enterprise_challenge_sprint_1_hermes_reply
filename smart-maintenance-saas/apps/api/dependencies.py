from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from core.config.settings import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header_value: str = Security(api_key_header)):
    """
    FastAPI dependency to validate an API key provided in the `X-API-Key` HTTP header.

    This function serves as a security measure for API endpoints. It retrieves the
    API key sent by a client in the `X-API-Key` header and compares it against
    the `EXPECTED_API_KEY` defined in the application's settings (`core.config.settings.API_KEY`).

    Args:
        api_key_header_value (str): The value of the `X-API-Key` header, injected by FastAPI's
                                    security dependency system.

    Raises:
        HTTPException:
            - status.HTTP_403_FORBIDDEN: If the `X-API-Key` header is missing.
            - status.HTTP_403_FORBIDDEN: If the provided API key does not match the
                                         `EXPECTED_API_KEY`.

    Returns:
        str: The validated API key if it is correct. This return value can be used
             by the endpoint if needed, though often the act of not raising an
             exception is sufficient proof of authentication.
    """
    if not api_key_header_value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated: X-API-Key header missing."
        )

    expected_api_key = settings.API_KEY

    if api_key_header_value != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key."
        )
    return api_key_header_value # Or True, or some other indicator of success
