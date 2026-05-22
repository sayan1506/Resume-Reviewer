"""Property-based tests for OAuth environment variable validation.

Feature: google-oauth, Property 9: Environment Variable Validation
Validates: Requirements 7.4
"""

import os
from unittest.mock import patch

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from utils.oauth_config import validate_oauth_config, REQUIRED_OAUTH_ENV_VARS


# Strategy: generate a non-empty proper subset of required env vars to be "present"
# (at least one var must be missing for the property to apply)
@st.composite
def subset_of_env_vars_with_at_least_one_missing(draw):
    """Generate a subset of required env vars where at least one is missing/empty.

    Returns a tuple of (present_vars, missing_vars) where missing_vars is non-empty.
    """
    all_vars = REQUIRED_OAUTH_ENV_VARS  # ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]

    # For each var, decide if it's present (True) or missing (False)
    presence = draw(st.lists(st.booleans(), min_size=len(all_vars), max_size=len(all_vars)))

    present_vars = [var for var, is_present in zip(all_vars, presence) if is_present]
    missing_vars = [var for var, is_present in zip(all_vars, presence) if not is_present]

    # At least one must be missing
    assume(len(missing_vars) > 0)

    return present_vars, missing_vars


# Strategy: generate values that should be treated as "empty" (whitespace-only or empty string)
empty_values = st.sampled_from(["", " ", "  ", "\t", "\n", "  \t\n  "])

# Strategy: generate valid non-empty values for env vars
valid_values = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S"), blacklist_characters="\x00"),
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip() != "")


class TestEnvVarValidationProperty:
    """Property 9: Environment Variable Validation.

    For any subset of the required environment variables (GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI) where at least one is missing
    or empty, calling validate_oauth_config() SHALL raise a RuntimeError whose
    message identifies the missing variable(s).

    **Validates: Requirements 7.4**
    """

    @given(data=subset_of_env_vars_with_at_least_one_missing())
    @settings(max_examples=100)
    def test_missing_vars_raises_runtime_error_identifying_them(self, data):
        """validate_oauth_config() raises RuntimeError identifying all missing vars.

        **Validates: Requirements 7.4**
        """
        present_vars, missing_vars = data

        # Build environment: present vars get valid values, missing vars get empty string
        env = {}
        for var in present_vars:
            env[var] = "valid-test-value"
        for var in missing_vars:
            env[var] = ""

        with patch.dict(os.environ, env, clear=False):
            # Remove missing vars entirely to also cover the "unset" case
            for var in missing_vars:
                os.environ.pop(var, None)

            with pytest.raises(RuntimeError) as exc_info:
                validate_oauth_config()

            error_message = str(exc_info.value)

            # Every missing var must be identified in the error message
            for var in missing_vars:
                assert var in error_message, (
                    f"Expected '{var}' to be mentioned in error message, "
                    f"but got: {error_message}"
                )

            # Present vars should NOT be mentioned in the error message
            for var in present_vars:
                assert var not in error_message, (
                    f"Expected '{var}' NOT to be in error message (it was set), "
                    f"but got: {error_message}"
                )

    @given(empty_val=empty_values)
    @settings(max_examples=100)
    def test_empty_or_whitespace_values_treated_as_missing(self, empty_val):
        """Whitespace-only or empty values are treated as missing.

        **Validates: Requirements 7.4**
        """
        # Set one var to an empty/whitespace value, others to valid values
        env = {
            "GOOGLE_CLIENT_ID": "valid-client-id",
            "GOOGLE_CLIENT_SECRET": empty_val,
            "GOOGLE_REDIRECT_URI": "http://localhost:8000/callback",
        }

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(RuntimeError) as exc_info:
                validate_oauth_config()

            error_message = str(exc_info.value)
            assert "GOOGLE_CLIENT_SECRET" in error_message

    @given(
        client_id=valid_values,
        client_secret=valid_values,
        redirect_uri=valid_values,
    )
    @settings(max_examples=100)
    def test_all_vars_present_does_not_raise(self, client_id, client_secret, redirect_uri):
        """When all required env vars are set with non-empty values, no error is raised.

        **Validates: Requirements 7.4**
        """
        env = {
            "GOOGLE_CLIENT_ID": client_id,
            "GOOGLE_CLIENT_SECRET": client_secret,
            "GOOGLE_REDIRECT_URI": redirect_uri,
        }

        with patch.dict(os.environ, env, clear=False):
            # Should not raise
            validate_oauth_config()
