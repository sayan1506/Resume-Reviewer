import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiSend, FiMessageCircle, FiAlertTriangle } from 'react-icons/fi';
import api from '../api/axios';
import Navbar from '../components/Navbar';
import InterviewScoreCard from '../components/InterviewScoreCard';
import InterviewSummary from '../components/InterviewSummary';

const SUGGESTION_CHIPS = [
  'What are my biggest weaknesses?',
  'How can I improve my project descriptions?',
  'Am I ready for a software engineering role?',
  'What skills should I learn next?',
];

export default function ChatPage() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hi! I'm your Resume AI assistant. Ask me anything about your resume review — strengths, weaknesses, how to improve, and more.",
      model_used: null,
      fallback_warning: null,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState('gemini');

  // --- Mock Interview state ---
  const [mode, setMode] = useState('chat');               // 'chat' | 'interview'
  const [interviewConfig, setInterviewConfig] = useState({
    jobDescription: '',
    numQuestions: 5,
    interviewType: 'mixed',
  });
  const [interviewPhase, setInterviewPhase] = useState('setup');
  // phases: 'setup' | 'questioning' | 'awaiting_feedback' | 'complete'

  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);  // {text, type, index, total}
  // Latest feedback / summary are rendered via message bubbles; we only keep the setters.
  const [, setLastFeedback] = useState(null);        // QuestionFeedback object
  const [, setSessionSummary] = useState(null);      // SessionSummary object
  const [interviewLoading, setInterviewLoading] = useState(false);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, interviewLoading]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (text) => {
    const userMessage = (text || input).trim();
    if (!userMessage || loading) return;

    // Add user message
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userMessage, model_used: null, fallback_warning: null },
    ]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.post('/ai/chat', {
        resume_id: parseInt(resumeId),
        message: userMessage,
        model: model,
      });

      const data = response.data;

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          model_used: data.model_used,
          fallback_warning: data.fallback_warning || null,
        },
      ]);
    } catch (err) {
      const status = err.response?.status;
      let errorContent;

      if (status === 429) {
        errorContent = '⚠ Rate limit reached (20/hour). Please wait a bit before sending more messages.';
      } else if (status === 404) {
        errorContent = '⚠ No analysis found. Please run a review first.';
      } else {
        errorContent =
          '⚠ ' + (err.response?.data?.detail || 'Something went wrong. Please try again.');
      }

      setMessages((prev) => [
        ...prev,
        { role: 'system', content: errorContent, model_used: null, fallback_warning: null },
      ]);
    } finally {
      setLoading(false);
      // Re-focus input after response
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  // --- Mock Interview handlers ---

  const handleStartInterview = async () => {
    setInterviewLoading(true);
    try {
      const res = await api.post('/ai/mock-interview/start', {
        resume_id: parseInt(resumeId),
        job_description: interviewConfig.jobDescription || null,
        model,
        num_questions: interviewConfig.numQuestions,
        interview_type: interviewConfig.interviewType,
      });
      const d = res.data;
      setSessionId(d.session_id);
      setCurrentQuestion({
        text: d.first_question,
        type: d.question_type,
        index: d.question_index,
        total: d.total_questions,
      });
      setInterviewPhase('questioning');
      setMessages([{
        role: 'assistant',
        content: d.first_question,
        meta: { type: 'interview_question', questionIndex: 0, questionType: d.question_type },
      }]);
    } catch (err) {
      const status = err.response?.status;
      if (status === 429) {
        alert('Rate limit: you can start 5 interviews per hour. Please wait.');
      } else {
        alert(err.response?.data?.detail || 'Failed to start interview. Try again.');
      }
    } finally {
      setInterviewLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    const userAnswer = input.trim();
    if (!userAnswer || interviewLoading) return;

    // Optimistically add user bubble
    setMessages((prev) => [...prev, { role: 'user', content: userAnswer }]);
    setInput('');
    setInterviewLoading(true);
    setInterviewPhase('awaiting_feedback');

    try {
      const res = await api.post('/ai/mock-interview/answer', {
        session_id: sessionId,
        answer: userAnswer,
        model,
      });
      const fb = res.data;
      setLastFeedback(fb);

      // Add score card as a special assistant bubble
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: null,                         // rendered by InterviewScoreCard, not as text
          meta: { type: 'score_card', feedback: fb },
        },
      ]);

      if (fb.is_complete) {
        setSessionSummary(fb.session_summary);
        setInterviewPhase('complete');
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: null,
            meta: { type: 'summary', summary: fb.session_summary },
          },
        ]);
      } else {
        // Advance to next question
        setCurrentQuestion({
          text: fb.next_question,
          type: fb.next_question_type,
          index: fb.question_index + 1,
          total: fb.total_questions,
        });
        setInterviewPhase('questioning');
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: fb.next_question,
            meta: { type: 'interview_question', questionIndex: fb.question_index + 1, questionType: fb.next_question_type },
          },
        ]);
      }
    } catch (err) {
      const status = err.response?.status;
      setMessages((prev) => [
        ...prev,
        {
          role: 'system',
          content: status === 429
            ? '⚠ Rate limit reached. Please wait before answering.'
            : '⚠ ' + (err.response?.data?.detail || 'Failed to evaluate answer. Try again.'),
        },
      ]);
      setInterviewPhase('questioning');   // let them retry
    } finally {
      setInterviewLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      mode === 'interview' ? handleSubmitAnswer() : sendMessage();
    }
  };

  const handleChipClick = (chip) => {
    sendMessage(chip);
  };

  const switchToChat = () => {
    setMode('chat');
    setInterviewPhase('setup');
  };

  const hasUserSent = messages.some((m) => m.role === 'user');
  const showChips = mode === 'chat' && !hasUserSent && !loading;
  const isBusy = loading || interviewLoading;
  const inputDisabled =
    isBusy || (mode === 'interview' && interviewPhase === 'awaiting_feedback');

  return (
    <>
      <Navbar />
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <button className="btn-back" onClick={() => navigate('/dashboard')}>
            <FiArrowLeft /> Back
          </button>
          <div className="chat-header-info">
            <h1>
              <FiMessageCircle className="chat-header-icon" />
              Chat with your Resume Analysis
            </h1>
            <p>Resume #{resumeId} · Ask follow-up questions or run a mock interview</p>
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="chat-mode-toggle">
          <button
            className={`mode-btn ${mode === 'chat' ? 'active' : ''}`}
            onClick={switchToChat}
            type="button"
          >
            💬 Chat
          </button>
          <button
            className={`mode-btn ${mode === 'interview' ? 'active' : ''}`}
            onClick={() => setMode('interview')}
            type="button"
          >
            🎤 Mock Interview
          </button>
        </div>

        {/* Interview Setup Panel */}
        {mode === 'interview' && interviewPhase === 'setup' && (
          <div className="interview-setup-panel">
            <h2>Mock Interview Setup</h2>
            <p className="interview-setup-hint">
              The AI will ask you questions based on your resume, evaluate each answer, and give
              per-question feedback. At the end you'll receive a full scorecard.
            </p>

            <label>Job Description <span className="optional-tag">(optional)</span></label>
            <textarea
              className="interview-jd-input"
              placeholder="Paste the job description here to get more targeted questions…"
              value={interviewConfig.jobDescription}
              onChange={(e) => setInterviewConfig((c) => ({ ...c, jobDescription: e.target.value }))}
              rows={4}
            />

            <div className="interview-setup-row">
              <div className="interview-setup-field">
                <label>Number of Questions</label>
                <select
                  value={interviewConfig.numQuestions}
                  onChange={(e) => setInterviewConfig((c) => ({ ...c, numQuestions: Number(e.target.value) }))}
                >
                  {[3, 5, 7, 10].map((n) => <option key={n} value={n}>{n} questions</option>)}
                </select>
              </div>

              <div className="interview-setup-field">
                <label>Question Type</label>
                <select
                  value={interviewConfig.interviewType}
                  onChange={(e) => setInterviewConfig((c) => ({ ...c, interviewType: e.target.value }))}
                >
                  <option value="mixed">Mixed</option>
                  <option value="technical">Technical only</option>
                  <option value="behavioral">Behavioral only</option>
                </select>
              </div>
            </div>

            <button
              className="btn-start-interview"
              onClick={handleStartInterview}
              disabled={interviewLoading}
            >
              {interviewLoading ? 'Generating questions…' : '▶ Start Mock Interview'}
            </button>
          </div>
        )}

        {/* Messages Area — hidden during interview setup */}
        {!(mode === 'interview' && interviewPhase === 'setup') && (
          <div className="chat-messages" id="chat-messages-area">
            {messages.map((msg, index) => {
              // Special interview bubbles
              if (msg.meta?.type === 'interview_question') {
                return (
                  <div key={index} className="chat-bubble-wrapper chat-bubble-assistant">
                    <div className="chat-avatar chat-avatar-ai">AI</div>
                    <div className="chat-bubble chat-bubble--assistant interview-question-bubble">
                      <div className="interview-q-label">
                        {msg.meta.questionType === 'technical' ? '⚙ Technical Question' : '💬 Behavioral Question'}
                      </div>
                      <div className="chat-bubble-content">{msg.content}</div>
                    </div>
                  </div>
                );
              }

              if (msg.meta?.type === 'score_card') {
                return <InterviewScoreCard key={index} feedback={msg.meta.feedback} />;
              }

              if (msg.meta?.type === 'summary') {
                return <InterviewSummary key={index} summary={msg.meta.summary} />;
              }

              return (
                <div key={index} className={`chat-bubble-wrapper chat-bubble-${msg.role}`}>
                  {msg.role === 'assistant' && (
                    <div className="chat-avatar chat-avatar-ai">AI</div>
                  )}
                  <div className={`chat-bubble chat-bubble--${msg.role}`}>
                    {msg.role === 'system' ? (
                      <div className="chat-system-message">
                        <FiAlertTriangle className="chat-system-icon" />
                        <span>{msg.content}</span>
                      </div>
                    ) : (
                      <div className="chat-bubble-content">{msg.content}</div>
                    )}
                    {msg.fallback_warning && (
                      <div className="chat-fallback-warning">
                        ⚠ {msg.fallback_warning}
                      </div>
                    )}
                    {msg.model_used && msg.role === 'assistant' && (
                      <div className="chat-model-badge">
                        via {msg.model_used === 'gemini' ? 'Gemini' : 'GPT'}
                      </div>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="chat-avatar chat-avatar-user">You</div>
                  )}
                </div>
              );
            })}

            {/* Typing Indicator */}
            {isBusy && (
              <div className="chat-bubble-wrapper chat-bubble-assistant">
                <div className="chat-avatar chat-avatar-ai">AI</div>
                <div className="chat-bubble chat-bubble--assistant">
                  <div className="chat-typing-indicator">
                    <span className="chat-typing-dot"></span>
                    <span className="chat-typing-dot"></span>
                    <span className="chat-typing-dot"></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Suggestion Chips — chat mode only, before first user message */}
        {showChips && (
          <div className="chat-suggestions">
            {SUGGESTION_CHIPS.map((chip, i) => (
              <button
                key={i}
                className="chat-chip"
                onClick={() => handleChipClick(chip)}
                type="button"
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {/* Interview Progress Bar */}
        {mode === 'interview' && interviewPhase !== 'setup' && currentQuestion && (
          <div className="interview-progress">
            <span>Question {currentQuestion.index + 1} of {currentQuestion.total}</span>
            <div className="interview-progress-bar">
              <div
                className="interview-progress-fill"
                style={{ width: `${((currentQuestion.index + 1) / currentQuestion.total) * 100}%` }}
              />
            </div>
            <span className={`question-type-badge badge-${currentQuestion.type}`}>
              {currentQuestion.type === 'technical' ? '⚙ Technical' : '💬 Behavioral'}
            </span>
          </div>
        )}

        {/* Input Area — hidden during interview setup and after completion */}
        {!(mode === 'interview' && (interviewPhase === 'setup' || interviewPhase === 'complete')) && (
          <div className="chat-input-area">
            {/* Model Toggle */}
            <div className="chat-model-toggle">
              <button
                className={`model-btn ${model === 'gemini' ? 'active' : ''}`}
                onClick={() => setModel('gemini')}
                type="button"
                disabled={isBusy}
              >
                Gemini
              </button>
              <button
                className={`model-btn ${model === 'gpt' ? 'active' : ''}`}
                onClick={() => setModel('gpt')}
                type="button"
                disabled={isBusy}
              >
                GPT
              </button>
            </div>

            <div className="chat-input-row">
              <textarea
                ref={inputRef}
                id="chat-input"
                className="chat-input"
                placeholder={
                  mode === 'interview' && interviewPhase === 'questioning'
                    ? 'Type your answer and press Enter to submit…'
                    : 'Ask about your resume…'
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={inputDisabled}
                rows={1}
              />
              <button
                id="chat-send-btn"
                className="chat-send-btn"
                onClick={() => (mode === 'interview' ? handleSubmitAnswer() : sendMessage())}
                disabled={inputDisabled || !input.trim()}
                type="button"
              >
                <FiSend />
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
