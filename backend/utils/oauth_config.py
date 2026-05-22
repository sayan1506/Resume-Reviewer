"""OAuth configuration validation utility."""

import os


REQUIRED_OAUTH_ENV_VARS = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI",
]


def validate_oauth_config() -> None:
    """Validate that all required OAuth environment variables are set and non-empty.

    Raises:
        RuntimeError: If any required environment variable is missing or empty,
            with a message identifying the missing variable(s).
    """
    missing = [
        var for var in REQUIRED_OAUTH_ENV_VARS
        if not os.environ.get(var, "").strip()
    ]

    if missing:
        raise RuntimeError(
            f"Missing required OAuth environment variable(s): {', '.join(missing)}"
        )
