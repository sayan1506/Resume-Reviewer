"""Per-request user context (locale + timezone) injected into AI prompts.

The frontend sends the browser's locale and IANA timezone as headers. They let
the model read ambiguous numeric dates correctly (05/06/2025 is 5 June in India
but May 6 in the US), judge dates against the user's real "today" instead of its
training cutoff, and apply the resume conventions of the user's region.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Request

LOCALE_HEADER = "X-User-Locale"
TIMEZONE_HEADER = "X-User-Timezone"

# BCP 47-ish tag, e.g. "en", "en-IN", "zh-Hant-TW". Anything else is dropped so
# header values can never smuggle text into the prompt.
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,3}$")

# Browsers in India often report "en-US", so the timezone is a better country
# signal than the language tag. Only regions we have norms for are listed.
_TZ_COUNTRY = {
    "Asia/Kolkata": "IN", "Asia/Calcutta": "IN",
    "Europe/London": "GB",
    "Europe/Berlin": "DE",
    "America/New_York": "US", "America/Chicago": "US", "America/Denver": "US",
    "America/Los_Angeles": "US", "America/Phoenix": "US", "America/Anchorage": "US",
    "Pacific/Honolulu": "US",
    "America/Toronto": "CA", "America/Vancouver": "CA", "America/Edmonton": "CA",
    "America/Winnipeg": "CA", "America/Halifax": "CA",
    "Australia/Sydney": "AU", "Australia/Melbourne": "AU", "Australia/Brisbane": "AU",
    "Australia/Perth": "AU", "Australia/Adelaide": "AU",
}

# Countries that write numeric dates month-first.
_MDY_COUNTRIES = {"US", "PH"}

_REGION_NORMS = {
    "IN": (
        "India: CGPA on a 10-point scale is standard (do not convert or penalize it). "
        "1 page for freshers, 2 pages for experienced candidates. A photo, date of birth "
        "or other personal details are common but optional; suggest removing them only as "
        "a minor tip. 'Fresher' is a normal term, and internships and academic projects "
        "carry real weight for freshers."
    ),
    "US": (
        "United States: GPA on a 4.0 scale. No photo, date of birth, age, marital status or "
        "nationality (anti-discrimination norms), so recommend removing them. 1 page for "
        "under ~10 years of experience."
    ),
    "CA": (
        "Canada: similar to the US. No photo, date of birth or marital status; "
        "1-2 pages; GPA scales vary by province and school, so do not penalize the scale used."
    ),
    "GB": (
        "United Kingdom: usually called a 'CV'; 2 pages is normal. Degree classifications "
        "(First, 2:1, 2:2) are used rather than GPA. No photo or date of birth."
    ),
    "AU": (
        "Australia: 2-3 pages is common. No photo or date of birth. Referees are often "
        "listed or marked 'available on request'."
    ),
    "DE": (
        "Germany: a professional photo and date of birth are still common and acceptable. "
        "Grades use the 1.0-5.0 scale where 1.0 is best. A tabular CV (Lebenslauf) is standard."
    ),
}

_GENERIC_NORMS = (
    "Region unknown: do not penalize a photo, date of birth, GPA/CGPA scale or page length "
    "purely on regional convention; mention such differences only as optional advice."
)


@dataclass(frozen=True)
class UserContext:
    locale: Optional[str] = None
    timezone: Optional[str] = None

    @property
    def country(self) -> Optional[str]:
        if self.timezone in _TZ_COUNTRY:
            return _TZ_COUNTRY[self.timezone]
        if self.locale:
            for part in reversed(self.locale.split("-")[1:]):
                if len(part) == 2 and part.isalpha():
                    return part.upper()
        return None


def _clean_locale(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    return value if len(value) <= 35 and _LOCALE_RE.match(value) else None


def _clean_timezone(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if len(value) > 64:
        return None
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        return None
    return value


def get_user_context(request: Request) -> UserContext:
    """FastAPI dependency: read and validate the locale/timezone headers."""
    return UserContext(
        locale=_clean_locale(request.headers.get(LOCALE_HEADER)),
        timezone=_clean_timezone(request.headers.get(TIMEZONE_HEADER)),
    )


def build_prompt_context(ctx: Optional[UserContext] = None, now: Optional[datetime] = None) -> str:
    """Render the user context block placed at the top of every AI prompt."""
    ctx = ctx or UserContext()
    tz_name = ctx.timezone or "UTC"
    today = (now or datetime.now(ZoneInfo(tz_name))).strftime("%d %B %Y")
    country = ctx.country

    if country in _MDY_COUNTRIES:
        date_order = "month first (MM/DD/YYYY), so 05/06/2025 means May 6, 2025"
    elif country:
        date_order = "day first (DD/MM/YYYY), so 05/06/2025 means 5 June 2025"
    else:
        date_order = (
            "unknown; infer it from other dates in the resume (e.g. 13/04/2024 can only be "
            "day first) and never flag an ambiguous date as an error"
        )

    norms = _REGION_NORMS.get(country, _GENERIC_NORMS)

    return f"""User context (trust this over assumptions from your training data):
- Today's date is {today} ({tz_name}). Your training data is older than this. Judge every date against today: dates on or before today are in the past, "Present"/"Current" means ongoing, and only dates after today are in the future.
- User locale: {ctx.locale or "unknown"}; region: {country or "unknown"}. Numeric date order: {date_order}.
- Regional resume conventions: {norms} If the resume or job description clearly targets a different country, apply that country's conventions instead."""
