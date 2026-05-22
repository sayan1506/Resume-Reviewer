"""Unit tests for OAuth environment validation utility."""

import os
import pytest
from unittest.mock import patch

from utils.oauth_config import validate_oauth_config


class TestValidateOauthConfig:
    """Tests for validate_oauth_config function."""

    def test_all_vars_set_passes(self):
        """No error when all required env vars are set and non-empty."""
        env = {
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret",
            "GOOGLE_REDIRECT_URI": "http://localhost:8000/callback",
        }
        with patch.dict(os.environ, env, clear=False):
            # Should not raise
            validate_oauth_config()

    def test_missing_all_vars_raises(self):
        """RuntimeError raised listing all vars when none are set."""
        env = {k: "" for k in [
            "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"
        ]}
        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(RuntimeError) as exc_info:
                validate_oauth_config()
            msg = str(exc_info.value)
            assert "GOOGLE_CLIENT_ID" in msg
            assert "GOOGLE_CLIENT_SECRET" in msg
            assert "GOOGLE_REDIRECT_URI" in msg

    def test_missing_single_var_raises(self):
        """RuntimeError raised identifying the single missing var."""
        env = {
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "",
            "GOOGLE_REDIRECT_URI": "http://localhost:8000/callback",
        }
        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(RuntimeError) as exc_info:
                validate_oauth_config()
            msg = str(exc_info.value)
            assert "GOOGLE_CLIENT_SECRET" in msg
            assert "GOOGLE_CLIENT_ID" not in msg
            assert "GOOGLE_REDIRECT_URI" not in msg

    def test_whitespace_only_treated_as_empty(self):
        """Whitespace-only values are treated as missing."""
        env = {
            "GOOGLE_CLIENT_ID": "   ",
            "GOOGLE_CLIENT_SECRET": "valid-secret",
            "GOOGLE_REDIRECT_URI": "\t",
        }
        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(RuntimeError) as exc_info:
                validate_oauth_config()
            msg = str(exc_info.value)
            assert "GOOGLE_CLIENT_ID" in msg
            assert "GOOGLE_REDIRECT_URI" in msg
            assert "GOOGLE_CLIENT_SECRET" not in msg

    def test_unset_var_treated_as_missing(self):
        """Variables not in os.environ at all are treated as missing."""
        # Clear all three vars from environment
        env_clear = {}
        for var in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]:
            env_clear[var] = ""
        with patch.dict(os.environ, env_clear, clear=False):
            # Remove them entirely
            for var in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]:
                os.environ.pop(var, None)
            with pytest.raises(RuntimeError) as exc_info:
                validate_oauth_config()
            msg = str(exc_info.value)
            assert "GOOGLE_CLIENT_ID" in msg
            assert "GOOGLE_CLIENT_SECRET" in msg
            assert "GOOGLE_REDIRECT_URI" in msg
