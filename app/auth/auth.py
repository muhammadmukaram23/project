from fastapi import Depends, Header, HTTPException, status

HARDCODED_TOKEN = "1"

def verify_token(api_authorization: str = Header(..., alias="API-Authorization")):
    if api_authorization != HARDCODED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )