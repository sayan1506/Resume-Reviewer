from datetime import date, datetime

from ai.context import UserContext, build_prompt_context
from utils.date_ranges import extract_date_ranges, format_months

TODAY = date(2026, 10, 22)

RESUME = """Jane Doe
EXPERIENCE
Software Intern, Acme Corp            Jun 2026 – Aug 2026
Backend Developer, Foo Labs           Jan 2023 - Present
Freelance Web Dev                     03/2022 – 12/2023
Upcoming SDE Intern                   Jan 2027 - Jun 2027
EDUCATION
B.Tech CSE, XYZ University            2022-26   CGPA 8.9
PROJECTS
Resume Reviewer                       Mar 2025 – Present
VOLUNTEER EXPERIENCE
NSS Volunteer                         Jan '21 – Dec '21
Phone +91 98765 43210
"""


def _by_text(summary):
    return {r.text: r for r in summary.ranges}


def test_recent_internship_is_completed_not_future():
    # The original bug: 2026 dates looked "future" to the model.
    r = _by_text(extract_date_ranges(RESUME, TODAY))["Jun 2026 – Aug 2026"]
    assert r.months == 3 and r.status == "completed" and r.section == "experience"


def test_present_is_counted_to_today():
    r = _by_text(extract_date_ranges(RESUME, TODAY))["Jan 2023 - Present"]
    assert r.months == 46 and r.status == "ongoing"
    assert format_months(r.months) == "3 years 10 months"


def test_upcoming_role_is_flagged_and_excluded_from_total():
    summary = extract_date_ranges(RESUME, TODAY)
    assert _by_text(summary)["Jan 2027 - Jun 2027"].status == "upcoming (starts after today)"
    # Mar 2022 to Oct 2026 with overlaps merged; projects, education,
    # volunteering and the upcoming role don't count.
    assert summary.total_months == 56


def test_sections_are_assigned():
    sections = {r.text: r.section for r in extract_date_ranges(RESUME, TODAY).ranges}
    assert sections["2022-26"] == "education"
    assert sections["Mar 2025 – Present"] == "projects"
    assert sections["Jan '21 – Dec '21"] == "other"


def test_year_only_ranges_are_approximate():
    r = _by_text(extract_date_ranges(RESUME, TODAY))["2022-26"]
    assert r.approximate and r.months == 48
    assert format_months(r.months, r.approximate) == "about 4 years"


def test_ambiguous_numeric_date_depends_on_region():
    text = "EXPERIENCE\nResearch Intern 05/06/2025 - 05/09/2025"
    assert extract_date_ranges(text, TODAY).ranges == ()  # region unknown: skipped
    assert extract_date_ranges(text, TODAY, day_first=True).ranges[0].months == 4    # Jun-Sep
    assert extract_date_ranges(text, TODAY, day_first=False).ranges[0].months == 1   # May 6-9


def test_unambiguous_numeric_date_needs_no_region():
    text = "EXPERIENCE\nIntern 15/01/2025 - 20/03/2025"
    assert extract_date_ranges(text, TODAY).ranges[0].months == 3


def test_non_dates_and_reversed_ranges_are_ignored():
    text = "EXPERIENCE\nCall +91 98765 43210\nScored 1200 - 1400\nDev Dec 2024 - Jan 2023"
    assert extract_date_ranges(text, TODAY).ranges == ()


def test_no_dates_gives_no_total():
    summary = extract_date_ranges("Skills: Python, SQL", TODAY)
    assert summary.ranges == () and summary.total_months is None


def test_prompt_context_includes_computed_facts():
    text = build_prompt_context(
        UserContext("en-US", "Asia/Kolkata"), now=datetime(2026, 10, 22), resume_text=RESUME
    )
    assert '"Jan 2023 - Present" (experience): 3 years 10 months, ongoing' in text
    assert "Total work experience" in text and "4 years 8 months" in text


def test_prompt_context_without_resume_has_no_date_facts():
    assert "Date ranges found" not in build_prompt_context(None)
    assert "Date ranges found" not in build_prompt_context(None, resume_text="Skills: Python")
