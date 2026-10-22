"""Find date ranges in resume text and compute their durations in code.

LLMs often miscount spans like "Jan 2023 – Present", so each range's duration,
its status (completed / ongoing / upcoming) and the total work experience are
worked out here and handed to the model as facts.
"""
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

MAX_RANGES = 20

_MONTH_NUMBERS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_SP = r"[^\S\n]*"  # spaces/tabs only, so a range never spans two lines
_DAY = r"\d{1,2}(?:st|nd|rd|th)?"
_MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
    r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
)
_YEAR = r"(?:19|20)\d{2}"
_POINT = (
    rf"(?:\d{{1,2}}[/.\-]\d{{1,2}}[/.\-]{_YEAR}"                       # 05/06/2025
    rf"|(?:{_DAY}{_SP})?{_MONTH}{_SP}(?:{_DAY}{_SP})?,?{_SP}(?:{_YEAR}|['’]\d{{2}})"  # Jan 2023, 15 Mar 2024, Mar 15, 2024, Jan '23
    rf"|\d{{1,2}}[/.\-]{_YEAR}"                                        # 05/2023
    rf"|{_YEAR})"                                                      # 2023
)
_PRESENT = rf"(?:present|current(?:ly)?|now|ongoing|today|(?:till|to){_SP}date|date)"
_SEP = rf"{_SP}(?:-|–|—|‒|~|to|till|until){_SP}"
_RANGE_RE = re.compile(
    rf"\b(?P<start>{_POINT})\b{_SEP}(?P<end>{_POINT}|{_PRESENT}|\d{{2}})\b",
    re.IGNORECASE,
)

# Headings decide which section a range belongs to. Order matters: the first
# match wins, so "Volunteer Experience" is not counted as work experience.
_HEADINGS = [
    ("education", re.compile(r"\b(education|academics?|academic background|qualifications?|schooling)\b", re.I)),
    ("projects", re.compile(r"\bprojects?\b", re.I)),
    ("other", re.compile(r"\bvolunteer\w*\b", re.I)),
    ("experience", re.compile(r"\b(experience|employment|work history|internships?|career history)\b", re.I)),
    ("other", re.compile(
        r"\b(skills|certifications?|achievements?|awards?|publications?|activities|extra[- ]?curricular"
        r"|leadership|positions? of responsibility|hobbies|interests|languages|summary|objective|profile"
        r"|references?)\b", re.I)),
]


@dataclass(frozen=True)
class DateRange:
    text: str           # the range as written, e.g. "Jan 2023 - Present"
    section: str        # experience | education | projects | other | unlabelled
    months: int
    approximate: bool   # True when a year-only date was involved
    status: str


@dataclass(frozen=True)
class DateRangeSummary:
    ranges: tuple[DateRange, ...]
    total_months: Optional[int]   # experience-section ranges, overlaps merged; None if none found
    total_approximate: bool


def _ordinal(year: int, month: int) -> int:
    return year * 12 + month - 1


def _label(ordinal: int, precise: bool) -> str:
    year, month0 = divmod(ordinal, 12)
    return f"{_MONTH_LABELS[month0]} {year}" if precise else str(year)


def _valid(year: int, month: Optional[int], precise: bool, today: date):
    if month and 1 <= month <= 12 and 1950 <= year <= today.year + 5:
        return year, month, precise
    return None


def _parse_point(raw: str, today: date, day_first: Optional[bool]):
    """Return (year, month, precise) for one date, or None if it can't be read."""
    t = raw.strip().lower()

    m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", t)
    if m:
        a, b, year = int(m[1]), int(m[2]), int(m[3])
        if a > 12 >= b:
            month = b
        elif b > 12 >= a:
            month = a
        elif day_first is None:
            return None  # ambiguous like 05/06/2025 and the region is unknown
        else:
            month = b if day_first else a
        return _valid(year, month, True, today)

    if re.search(r"[a-z]", t):
        word = re.search(r"[a-z]{3,}", t)
        month = _MONTH_NUMBERS.get(word[0][:3]) if word else None
        full = re.search(r"\d{4}", t)
        if full:
            year = int(full[0])
        else:
            short = re.search(r"['’](\d{2})", t)
            if not short:
                return None
            year = 2000 + int(short[1])
            if year > today.year + 5:
                year -= 100
        return _valid(year, month, True, today)

    m = re.fullmatch(r"(\d{1,2})[/.\-](\d{4})", t)
    if m:
        return _valid(int(m[2]), int(m[1]), True, today)

    if re.fullmatch(r"\d{4}", t):
        return _valid(int(t), 1, False, today)
    return None


def _heading_section(line: str) -> Optional[str]:
    text = line.strip().strip(":").strip()
    if not text or len(text) > 40 or len(text.split()) > 4 or re.search(r"\d", text):
        return None
    for section, pattern in _HEADINGS:
        if pattern.search(text):
            return section
    return None


def _parse_range(start_raw: str, end_raw: str, today: date, day_first: Optional[bool]):
    start = _parse_point(start_raw, today, day_first)
    if not start:
        return None
    start_year, start_month, start_precise = start
    start_ord = _ordinal(start_year, start_month)
    today_ord = _ordinal(today.year, today.month)
    end_text = end_raw.strip().lower()

    if re.fullmatch(_PRESENT, end_text, re.IGNORECASE):
        end_ord, end_precise, ongoing = today_ord, True, True
    elif re.fullmatch(r"\d{2}", end_text):
        if start_precise:
            return None  # "Jan 2023 - 15" is not a range we understand
        end_year = start_year // 100 * 100 + int(end_text)  # "2022-26" -> 2026
        if end_year < start_year:
            end_year += 100
        if end_year > today.year + 5:
            return None
        end_ord, end_precise, ongoing = _ordinal(end_year, 1), False, False
    else:
        end = _parse_point(end_raw, today, day_first)
        if not end:
            return None
        end_ord, end_precise, ongoing = _ordinal(end[0], end[1]), end[2], False

    if end_ord < start_ord:
        return None

    # Months are counted inclusively (Jan-Mar = 3). Two year-only dates are
    # read as whole years instead (2021-2023 = about 2 years).
    if start_precise or end_precise:
        months = end_ord - start_ord + 1
    else:
        months = end_ord - start_ord

    if ongoing:
        status = "ongoing"
    elif start_ord > today_ord:
        status = "upcoming (starts after today)"
    elif end_ord > today_ord:
        status = f"in progress, planned to end {_label(end_ord, end_precise)}"
    else:
        status = "completed"

    return start_ord, months, not (start_precise and end_precise), status, ongoing


def extract_date_ranges(text: Optional[str], today: date, day_first: Optional[bool] = None) -> DateRangeSummary:
    """Find date ranges in resume text and compute durations relative to today.

    day_first decides ambiguous full dates like 05/06/2025 (True = DD/MM,
    False = MM/DD, None = region unknown, so ambiguous dates are skipped).
    """
    today_ord = _ordinal(today.year, today.month)
    ranges: list[DateRange] = []
    work_intervals: list[tuple[int, int]] = []
    work_approximate = False
    seen = set()
    section = "unlabelled"

    for line in (text or "").splitlines():
        heading = _heading_section(line)
        if heading:
            section = heading
            continue
        for match in _RANGE_RE.finditer(line):
            parsed = _parse_range(match["start"], match["end"], today, day_first)
            if not parsed:
                continue
            start_ord, months, approximate, status, ongoing = parsed
            key = (start_ord, months, ongoing, section)
            if key in seen:
                continue
            seen.add(key)
            ranges.append(DateRange(
                text=re.sub(r"\s+", " ", match[0]).strip(),
                section=section,
                months=months,
                approximate=approximate,
                status=status,
            ))
            if section == "experience" and start_ord <= today_ord:
                work_intervals.append((start_ord, min(start_ord + months, today_ord + 1)))
                work_approximate = work_approximate or approximate
            if len(ranges) >= MAX_RANGES:
                break
        if len(ranges) >= MAX_RANGES:
            break

    total = None
    if work_intervals:
        total = 0
        current_start, current_end = None, None
        for start, end in sorted(work_intervals):
            if current_end is None or start > current_end:
                if current_end is not None:
                    total += current_end - current_start
                current_start, current_end = start, end
            else:
                current_end = max(current_end, end)
        total += current_end - current_start

    return DateRangeSummary(tuple(ranges), total, work_approximate)


def format_months(months: int, approximate: bool = False) -> str:
    if months <= 0:
        return "under 1 year"
    years, rest = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if rest:
        parts.append(f"{rest} month{'s' if rest != 1 else ''}")
    text = " ".join(parts)
    return f"about {text}" if approximate else text
