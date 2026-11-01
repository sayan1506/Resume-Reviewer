from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from schemas.ai_schema import AIReviewResponse
from services import ai_service
from services.ai_service import _consistency_clause


def test_no_previous_review_adds_nothing():
    assert _consistency_clause(None) == ""


def test_previous_review_anchors_score():
    prev = SimpleNamespace(score=72, created_at=datetime(2026, 10, 20, tzinfo=timezone.utc))
    clause = _consistency_clause(prev)
    assert "scored 72/100" in clause
    assert "20 October 2026" in clause
    assert "within about 5 points of 72" in clause
    assert "state that reason" in clause


def _run_review(previous, target_role=None, seniority=None):
    resume = SimpleNamespace(id=1, parsed_text="EXPERIENCE\nDev Jan 2023 - Present")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = resume
    llm_out = AIReviewResponse(score=75, strengths=["a"], weaknesses=["b"], suggestions=["c"])
    captured = {}

    def fake_invoke(model_choice, chain_factory, inputs):
        captured.update(inputs)
        return SimpleNamespace(result=llm_out, model_used="gpt", fallback_warning=None)

    with patch.object(ai_service, "_previous_review", return_value=previous) as prev_mock, \
         patch.object(ai_service, "invoke_with_fallback", side_effect=fake_invoke), \
         patch.object(ai_service, "_fire_and_forget_embeddings"):
        result = ai_service.review_resume_service(
            1, 1, "gpt", db, target_role=target_role, seniority=seniority
        )
    saved = db.add.call_args[0][0]
    return result, saved, captured, prev_mock


def test_review_saves_role_and_level_and_returns_previous_score():
    prev = SimpleNamespace(score=70, created_at=datetime(2026, 10, 20, tzinfo=timezone.utc))
    result, saved, captured, prev_mock = _run_review(prev, "Backend Engineer", "junior")

    prev_mock.assert_called_once_with(prev_mock.call_args[0][0], 1, "Backend Engineer", "junior")
    assert saved.target_role == "Backend Engineer" and saved.seniority == "junior"
    assert result.target_role == "Backend Engineer" and result.seniority == "junior"
    assert result.previous_score == 70
    assert "scored 70/100" in captured["consistency_clause"]


def test_first_review_has_no_previous_score():
    result, saved, captured, _ = _run_review(None)
    assert result.previous_score is None
    assert captured["consistency_clause"] == ""
    assert saved.target_role is None and saved.seniority is None
