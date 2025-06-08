from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from core.config.settings import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header_value: str = Security(api_key_header)):
    """
    Dependency to validate the API key from the X-API-Key header.

    Reads the expected API_KEY from application settings.
    Raises HTTPException 403 if the key is missing or invalid.
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
