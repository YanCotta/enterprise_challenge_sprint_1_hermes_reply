from fastapi import Security, HTTPException, status, Depends
from fastapi.security import SecurityScopes
from fastapi.security.api_key import APIKeyHeader
from core.config.settings import settings

API_KEY_NAME = "X-API-Key" # Ensure this matches the client-side header name
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def api_key_auth(
    security_scopes: SecurityScopes,
    api_key_header_value: str = Security(api_key_header) # Corrected: api_key_header_value
):
    """
    FastAPI dependency to validate an API key and placeholder for RBAC scope checking.
    """
    # This is a basic API key check.
    # TODO: Enhance with actual RBAC, checking security_scopes against user/client permissions.
    if not api_key_header_value: # Corrected: check api_key_header_value
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated: API key required." # Updated detail
        )

    expected_api_key = settings.API_KEY
    if api_key_header_value != expected_api_key: # Corrected: compare api_key_header_value
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials: Invalid API key." # Updated detail
        )

    # Placeholder for scope logging/awareness
    if security_scopes.scopes:
        # In a real app, you'd use a proper logger here
        print(f"Required scopes: {security_scopes.scopes}")
        # Here you would add logic to check if the token (API key) has these scopes.
        # For now, we just log them.

    # Return a dictionary that could be used by the endpoint if needed,
    # e.g., to access user details or validated scopes.
    return {"api_key": api_key_header_value, "scopes": security_scopes.scopes}
