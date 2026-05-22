"""Property-based test for authorization code validation.

Feature: google-oauth, Property 6: Authorization Code Validation
Validates: Requirements 1.7, 1.8
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis.strategies import text, integers
from pydantic import ValidationError

from schemas.auth_schema import GoogleAuthRequest


class TestAuthorizationCodeValidation:
    """Property 6: Authorization Code Validation

    For any string input to the GoogleAuthRequest schema, the validation SHALL
    accept the input if and only if the string length is between 1 and 2048
    characters inclusive. Strings that are empty or exceed 2048 characters SHALL
    be rejected with a validation error.

    **Validates: Requirements 1.7, 1.8**
    """

    @given(length=integers(min_value=1, max_value=2048))
    @settings(max_examples=100)
    def test_valid_codes_accepted(self, length: int):
        """Codes with length 1-2048 are accepted by GoogleAuthRequest."""
        code = "a" * length
        request = GoogleAuthRequest(code=code)
        assert request.code == code
        assert len(request.code) == length

    @given(code=text(min_size=1, max_size=2048))
    @settings(max_examples=100)
    def test_valid_arbitrary_strings_accepted(self, code: str):
        """Any non-empty string up to 2048 chars is accepted."""
        request = GoogleAuthRequest(code=code)
        assert request.code == code

    @given(length=integers(min_value=2049, max_value=5000))
    @settings(max_examples=100)
    def test_oversized_codes_rejected(self, length: int):
        """Codes exceeding 2048 characters are rejected with ValidationError."""
        code = "a" * length
        with pytest.raises(ValidationError) as exc_info:
            GoogleAuthRequest(code=code)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_empty_string_rejected(self):
        """Empty string (length 0) is rejected with ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GoogleAuthRequest(code="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    @given(length=integers(min_value=0, max_value=5000))
    @settings(max_examples=100)
    def test_acceptance_iff_length_in_bounds(self, length: int):
        """GoogleAuthRequest accepts code iff 1 <= len(code) <= 2048."""
        code = "x" * length
        if 1 <= length <= 2048:
            request = GoogleAuthRequest(code=code)
            assert request.code == code
        else:
            with pytest.raises(ValidationError):
                GoogleAuthRequest(code=code)
