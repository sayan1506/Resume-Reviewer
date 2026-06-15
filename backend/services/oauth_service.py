import os

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import User
from schemas.auth_schema import GoogleUserInfo


async def exchange_google_code(code: str) -> GoogleUserInfo:
    """Exchange authorization code with Google and return user profile.

    Exchanges the code at Google's token endpoint, then fetches the user's
    profile from the userinfo endpoint.

    Raises:
        HTTPException(401): If the code is invalid or expired.
        HTTPException(502): If Google's endpoints time out or return non-2xx.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            token_response = await client.post(
                token_url,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=502,
                detail="Google authentication service is unavailable",
            )

        if token_response.status_code != 200:
            if token_response.status_code == 400 or token_response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Google authorization code is invalid or expired",
                )
            raise HTTPException(
                status_code=502,
                detail="Google authentication service is unavailable",
            )

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        try:
            userinfo_response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=502,
                detail="Google authentication service is unavailable",
            )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Google authentication service is unavailable",
            )

        userinfo = userinfo_response.json()

    email = userinfo.get("email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Google profile is missing required information",
        )

    return GoogleUserInfo(
        email=email,
        google_id=userinfo.get("sub", userinfo.get("id", "")),
        name=userinfo.get("name"),
        avatar_url=userinfo.get("picture"),
    )


def find_or_create_oauth_user(google_info: GoogleUserInfo, db: Session) -> User:
    """Find existing user by email/google_id or create new one. Handles account linking.

    Logic:
    1. Validate google_info.email and google_info.google_id are not None/empty.
    2. Check if a user with this google_id already exists → return that user.
    3. Check if a user with this email exists → check for google_id conflict (409),
       then link account (update google_id, avatar_url, auth_provider).
    4. Otherwise create new user with email, google_id, avatar_url, auth_provider="google",
       password=NULL.

    Raises:
        HTTPException(400): If email or google_id is missing/empty.
        HTTPException(409): If google_id is already linked to a different user.
    """
    # Step 1: Validate required fields
    if not google_info.email or not google_info.google_id:
        raise HTTPException(
            status_code=400,
            detail="Google profile is missing required information",
        )

    # Step 2: Check if a user with this google_id already exists
    existing_google_user = (
        db.query(User).filter(User.google_id == google_info.google_id).first()
    )
    if existing_google_user:
        # If the google_id is already linked to a user with a different email,
        # and there's another user with the incoming email, that's a conflict.
        if existing_google_user.email == google_info.email:
            return existing_google_user
        # The google_id belongs to a different user than the email suggests
        # Check if a user with the incoming email exists (conflict scenario)
        existing_email_user = (
            db.query(User).filter(User.email == google_info.email).first()
        )
        if existing_email_user:
            raise HTTPException(
                status_code=409,
                detail="This Google account is already linked to another user",
            )
        return existing_google_user

    # Step 3: Check if a user with this email already exists
    existing_email_user = (
        db.query(User).filter(User.email == google_info.email).first()
    )
    if existing_email_user:
        # Check for google_id conflict: if this user already has a different google_id
        # that shouldn't happen here since we already checked google_id lookup above.
        # But check if another user already has this google_id linked (conflict scenario).
        if existing_email_user.google_id and existing_email_user.google_id != google_info.google_id:
            raise HTTPException(
                status_code=409,
                detail="This Google account is already linked to another user",
            )

        # Link the Google account to the existing email user
        existing_email_user.google_id = google_info.google_id
        existing_email_user.avatar_url = google_info.avatar_url
        existing_email_user.auth_provider = "google"
        # Preserve existing password hash unchanged
        db.commit()
        db.refresh(existing_email_user)
        return existing_email_user

    # Step 4: Create new user
    new_user = User(
        email=google_info.email,
        google_id=google_info.google_id,
        avatar_url=google_info.avatar_url,
        auth_provider="google",
        password=None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
