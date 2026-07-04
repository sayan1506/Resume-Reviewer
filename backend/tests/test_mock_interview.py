"""Unit tests for the mock interview service.

These tests mock the LLM layer with real ``RunnableLambda`` objects so the
``prompt | llm.with_structured_output(...)`` chains execute end-to-end without
calling any external API.
"""
import os

# ai.llm constructs a ChatGoogleGenerativeAI at import time, which needs a key.
os.environ.setdefault("GOOGLE_API_KEY", "test-key")

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.runnables import RunnableLambda

from services.mock_interview_service import (
    start_mock_interview_service,
    answer_mock_question_service,
    QuestionList,
    AnswerEvaluation,
    SummaryText,
)
from schemas.mock_interview_schema import GeneratedQuestion
from ai.router import InvokeResult


def _structured_factory(question_obj=None, eval_obj=None, summary_obj=None):
    """Return a side_effect for ``with_structured_output`` that yields a real
    Runnable producing the right object for each schema."""
    def _wso(schema):
        if schema is QuestionList:
            return RunnableLambda(lambda _inp: question_obj)
        if schema is AnswerEvaluation:
            return RunnableLambda(lambda _inp: eval_obj)
        if schema is SummaryText:
            return RunnableLambda(lambda _inp: summary_obj)
        return RunnableLambda(lambda _inp: None)
    return _wso


def _fallback_side_effect(question_obj=None, eval_obj=None, summary_obj=None,
                          model_used="gpt", fallback_warning=None):
    """side_effect for ``invoke_with_fallback``: runs the real
    ``prompt | llm.with_structured_output(...)`` chain against a fake LLM and
    wraps the output the way the router would."""
    wso = _structured_factory(question_obj, eval_obj, summary_obj)

    def _invoke(model_choice, chain_factory, inputs):
        fake_llm = MagicMock()
        fake_llm.with_structured_output.side_effect = wso
        result = chain_factory(fake_llm).invoke(inputs)
        return InvokeResult(result=result, model_used=model_used,
                            fallback_warning=fallback_warning)

    return _invoke


@pytest.fixture
def db_mock():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


def make_resume(id=1, user_id=1, text="Python developer with FastAPI experience"):
    r = MagicMock()
    r.id, r.user_id, r.parsed_text = id, user_id, text
    return r


def test_start_returns_session_id(db_mock):
    q = QuestionList(questions=[
        GeneratedQuestion(question="Q1", type="technical", ideal_answer="A1")
    ])

    with patch("services.mock_interview_service._get_resume", return_value=make_resume()), \
         patch("services.mock_interview_service.invoke_with_fallback",
               side_effect=_fallback_side_effect(question_obj=q)):
        result = start_mock_interview_service(1, 1, None, "gpt", 1, "mixed", db_mock)

    assert result.session_id is not None
    assert result.first_question == "Q1"
    assert result.question_type == "technical"
    assert result.question_index == 0
    assert result.total_questions == 1
    db_mock.add.assert_called_once()
    db_mock.commit.assert_called_once()


def test_start_caps_questions_to_requested_count(db_mock):
    q = QuestionList(questions=[
        GeneratedQuestion(question=f"Q{i}", type="technical", ideal_answer="A")
        for i in range(5)
    ])

    with patch("services.mock_interview_service._get_resume", return_value=make_resume()), \
         patch("services.mock_interview_service.invoke_with_fallback",
               side_effect=_fallback_side_effect(question_obj=q)):
        result = start_mock_interview_service(1, 1, None, "gpt", 3, "mixed", db_mock)

    assert result.total_questions == 3


def test_answer_completes_single_question_session(db_mock):
    session = MagicMock()
    session.current_index = 0
    session.questions = [{"question": "Q1", "type": "technical", "ideal_answer": "A1"}]
    session.turns = []
    session.status = "active"
    db_mock.query.return_value.filter.return_value.first.return_value = session

    eval_obj = AnswerEvaluation(
        score=7, strengths=["Good"], improvements=["More depth"], ideal_answer_hint="Hint"
    )
    summary_obj = SummaryText(
        overall_feedback="Solid overall.", top_strength="Depth", top_improvement="Structure"
    )

    with patch("services.mock_interview_service.invoke_with_fallback",
               side_effect=_fallback_side_effect(eval_obj=eval_obj, summary_obj=summary_obj)):
        result = answer_mock_question_service("fake-uuid", 1, "My answer", "gpt", db_mock)

    assert result.is_complete is True
    assert result.score == 7
    assert result.next_question is None
    assert result.session_summary is not None
    assert result.session_summary.total_score == 7
    assert result.session_summary.max_score == 10
    assert result.session_summary.percentage == 70
    assert session.status == "complete"
    assert session.current_index == 1


def test_answer_advances_to_next_question(db_mock):
    session = MagicMock()
    session.current_index = 0
    session.questions = [
        {"question": "Q1", "type": "technical", "ideal_answer": "A1"},
        {"question": "Q2", "type": "behavioral", "ideal_answer": "A2"},
    ]
    session.turns = []
    session.status = "active"
    db_mock.query.return_value.filter.return_value.first.return_value = session

    eval_obj = AnswerEvaluation(
        score=5, strengths=["Clear"], improvements=["Add examples"], ideal_answer_hint="Hint"
    )

    with patch("services.mock_interview_service.invoke_with_fallback",
               side_effect=_fallback_side_effect(eval_obj=eval_obj)):
        result = answer_mock_question_service("fake-uuid", 1, "My answer", "gpt", db_mock)

    assert result.is_complete is False
    assert result.next_question == "Q2"
    assert result.next_question_type == "behavioral"
    assert result.question_index == 0
    assert result.session_summary is None
    assert session.current_index == 1
    assert session.status == "active"


def test_answer_rejects_completed_session(db_mock):
    from fastapi import HTTPException

    session = MagicMock()
    session.status = "complete"
    db_mock.query.return_value.filter.return_value.first.return_value = session

    with pytest.raises(HTTPException) as exc:
        answer_mock_question_service("fake-uuid", 1, "answer", "gemini", db_mock)
    assert exc.value.status_code == 400


def test_answer_missing_session_404(db_mock):
    from fastapi import HTTPException

    db_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        answer_mock_question_service("missing", 1, "answer", "gemini", db_mock)
    assert exc.value.status_code == 404
