import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  const [chatSessionId, setChatSessionId] = useState(null);

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
        session_id: chatSessionId,
      });

      const data = response.data;

      if (data.session_id) {
        setChatSessionId(data.session_id);
      }

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

  const hasUserSent = messages.some((m) => m.role === 'user');
  const showChips = mode === 'chat' && !hasUserSent && !loading;
  const isBusy = loading || interviewLoading;
  const inputDisabled =
    isBusy || (mode === 'interview' && interviewPhase === 'awaiting_feedback');

  return (
    <>
      <Navbar />
      <div className="flex flex-col h-[calc(100vh-64px)] max-w-3xl mx-auto">
        {/* chat header bar */}
        <div className="flex-shrink-0 px-margin-mobile sm:px-margin-desktop py-4 border-b border-slate-gray/10 bg-surface/60 backdrop-blur-md">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors text-label-md"
          >
            <span className="material-symbols-outlined text-[20px]">arrow_back</span>
            Dashboard
          </button>
          <div className="mt-2">
            <h1 className="font-display text-headline-md text-on-surface">Resume Reviewer</h1>
            <p className="text-label-sm text-on-surface-variant">
              Resume #{resumeId} · Chat or run a mock interview
            </p>
          </div>
        </div>

        {/* mode toggle */}
        <div className="flex-shrink-0 px-margin-mobile sm:px-margin-desktop py-3">
          <div className="inline-flex rounded-lg bg-surface-container p-1 gap-1">
            <button
              onClick={() => { setMode('chat'); setInterviewPhase('setup'); }}
              type="button"
              className={`px-6 py-2 rounded-lg text-label-md font-label-md transition-all flex items-center gap-2
                          ${mode === 'chat' ? 'bg-electric-indigo text-white shadow-md' : 'text-slate-gray hover:bg-surface-container-high'}`}
            >
              <span className="material-symbols-outlined text-[20px]">chat_bubble</span>
              Chat
            </button>
            <button
              onClick={() => setMode('interview')}
              type="button"
              className={`px-6 py-2 rounded-lg text-label-md font-label-md transition-all flex items-center gap-2
                          ${mode === 'interview' ? 'bg-electric-indigo text-white shadow-md' : 'text-slate-gray hover:bg-surface-container-high'}`}
            >
              <span className="material-symbols-outlined text-[20px]">psychology</span>
              Mock Interview
            </button>
          </div>
        </div>

        {/* interview setup panel */}
        {mode === 'interview' && interviewPhase === 'setup' && (
          <div className="flex-1 overflow-y-auto px-margin-mobile sm:px-margin-desktop pb-6">
            <div className="tonal-card rounded-2xl p-6">
              <h2 className="text-headline-md font-display text-on-surface">Mock Interview Setup</h2>
              <p className="mt-2 text-body-md text-on-surface-variant">
                The AI will ask questions based on your resume, evaluate each answer, and give
                per-question feedback. At the end you receive a full scorecard.
              </p>

              <div className="mt-6 space-y-4">
                <div>
                  <label className="flex items-center gap-1 mb-1.5 text-label-md text-on-surface-variant">
                    Job Description
                    <span className="text-label-sm text-on-surface-variant/60">(optional)</span>
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Paste the job description here to get more targeted questions…"
                    value={interviewConfig.jobDescription}
                    onChange={(e) => setInterviewConfig((c) => ({ ...c, jobDescription: e.target.value }))}
                    className="w-full p-4 rounded-lg border border-outline-variant bg-white resize-none
                               text-body-md outline-none focus:border-electric-indigo focus:ring-1 focus:ring-electric-indigo"
                  />
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block mb-1.5 text-label-md text-on-surface-variant">Number of Questions</label>
                    <select
                      value={interviewConfig.numQuestions}
                      onChange={(e) => setInterviewConfig((c) => ({ ...c, numQuestions: Number(e.target.value) }))}
                      className="w-full px-4 py-3 rounded-lg border border-outline-variant bg-white
                                 text-body-md outline-none focus:border-electric-indigo focus:ring-1 focus:ring-electric-indigo"
                    >
                      {[3, 5, 7, 10].map((n) => <option key={n} value={n}>{n} questions</option>)}
                    </select>
                  </div>

                  <div>
                    <label className="block mb-1.5 text-label-md text-on-surface-variant">Question Type</label>
                    <select
                      value={interviewConfig.interviewType}
                      onChange={(e) => setInterviewConfig((c) => ({ ...c, interviewType: e.target.value }))}
                      className="w-full px-4 py-3 rounded-lg border border-outline-variant bg-white
                                 text-body-md outline-none focus:border-electric-indigo focus:ring-1 focus:ring-electric-indigo"
                    >
                      <option value="mixed">Mixed</option>
                      <option value="technical">Technical only</option>
                      <option value="behavioral">Behavioral only</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleStartInterview}
                  disabled={interviewLoading}
                  className="w-full bg-electric-indigo text-white py-3.5 rounded-xl text-label-md font-label-md
                             flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-electric-indigo/20
                             active:scale-95 transition-all disabled:opacity-60"
                >
                  <span className="material-symbols-outlined text-[20px]">play_arrow</span>
                  {interviewLoading ? 'Generating questions…' : 'Start Mock Interview'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* messages area */}
        {!(mode === 'interview' && interviewPhase === 'setup') && (
          <div
            id="chat-messages-area"
            className="chat-scroll flex-1 overflow-y-auto px-margin-mobile sm:px-margin-desktop py-4 space-y-4"
          >
            {messages.map((msg, index) => {
              // interview question bubble
              if (msg.meta?.type === 'interview_question') {
                return (
                  <div key={index} className="flex justify-start">
                    <div className="max-w-[85%]">
                      <div className="flex items-center gap-1.5 mb-1 text-label-sm font-semibold text-electric-indigo">
                        <span className="material-symbols-outlined text-[18px]">
                          {msg.meta.questionType === 'technical' ? 'code' : 'groups'}
                        </span>
                        {msg.meta.questionType === 'technical' ? 'Technical' : 'Behavioral'}
                      </div>
                      <div className="tonal-card rounded-2xl rounded-bl-sm px-4 py-3 text-body-md text-on-surface">
                        {msg.content}
                      </div>
                    </div>
                  </div>
                );
              }
              // score card bubble
              if (msg.meta?.type === 'score_card') {
                return <InterviewScoreCard key={index} feedback={msg.meta.feedback} />;
              }
              // summary
              if (msg.meta?.type === 'summary') {
                return <InterviewSummary key={index} summary={msg.meta.summary} />;
              }

              // normal chat bubbles
              const isAI = msg.role === 'assistant';
              const isUser = msg.role === 'user';
              return (
                <div key={index} className={`flex items-end gap-2 ${isUser ? 'justify-end' : isAI ? 'justify-start' : 'justify-center'}`}>
                  {/* avatar */}
                  {isAI && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-indigo text-white flex items-center justify-center">
                      <span className="material-symbols-outlined text-[18px]">stars</span>
                    </div>
                  )}

                  <div className={`max-w-[75%] ${isUser ? 'order-1' : ''}`}>
                    {isAI && msg.model_used && (
                      <div className="text-label-sm text-on-surface-variant mb-1">
                        {msg.model_used === 'gpt5' ? 'GPT-5' : msg.model_used === 'gpt' ? 'GPT-4o' : 'Gemini AI'}
                      </div>
                    )}
                    <div
                      className={`px-4 py-3 text-body-md whitespace-pre-wrap break-words
                        ${isUser
                          ? 'bg-electric-indigo text-white rounded-2xl rounded-br-sm'
                          : msg.role === 'system'
                          ? 'bg-warning-amber/10 text-warning-amber rounded-xl'
                          : 'tonal-card text-on-surface rounded-2xl rounded-bl-sm'}`}
                    >
                      {msg.role === 'system' ? (
                        <div className="flex items-start gap-2">
                          <span className="material-symbols-outlined text-[20px]">warning</span>
                          <span>{msg.content}</span>
                        </div>
                      ) : msg.content}
                    </div>
                    {msg.fallback_warning && (
                      <div className="mt-1 text-label-sm text-warning-amber">
                        ⚠ {msg.fallback_warning}
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-container-high text-on-surface-variant
                                    flex items-center justify-center text-label-sm font-semibold">
                      You
                    </div>
                  )}
                </div>
              );
            })}

            {/* typing indicator */}
            {isBusy && (
              <div className="flex items-end gap-2 justify-start">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-indigo text-white flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px]">stars</span>
                </div>
                <div className="tonal-card rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1">
                  <span className="typing-dot w-2 h-2 rounded-full bg-on-surface-variant" />
                  <span className="typing-dot w-2 h-2 rounded-full bg-on-surface-variant" />
                  <span className="typing-dot w-2 h-2 rounded-full bg-on-surface-variant" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* suggestion chips (chat mode, before first message) */}
        {showChips && (
          <div className="flex-shrink-0 px-margin-mobile sm:px-margin-desktop pb-2 flex flex-wrap gap-2">
            {SUGGESTION_CHIPS.map((chip, i) => (
              <button
                key={i}
                onClick={() => handleChipClick(chip)}
                type="button"
                className="px-4 py-1.5 rounded-full border border-electric-indigo text-electric-indigo
                           text-label-md font-label-md hover:bg-electric-indigo hover:text-white
                           transition-all whitespace-nowrap"
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {/* interview progress bar */}
        {mode === 'interview' && interviewPhase !== 'setup' && currentQuestion && (
          <div className="flex-shrink-0 px-margin-mobile sm:px-margin-desktop py-2 flex items-center gap-3">
            <span className="text-label-sm text-on-surface-variant whitespace-nowrap">
              Question {currentQuestion.index + 1} of {currentQuestion.total}
            </span>
            <div className="flex-1 h-2 rounded-full bg-surface-container-high overflow-hidden">
              <div
                className="h-full bg-electric-indigo transition-all"
                style={{ width: `${((currentQuestion.index + 1) / currentQuestion.total) * 100}%` }}
              />
            </div>
            <span className="text-label-sm text-on-surface-variant whitespace-nowrap">
              {currentQuestion.type === 'technical' ? '⚙ Technical' : '💬 Behavioral'}
            </span>
          </div>
        )}

        {/* input area */}
        {!(mode === 'interview' && (interviewPhase === 'setup' || interviewPhase === 'complete')) && (
          <div className="flex-shrink-0 px-margin-mobile sm:px-margin-desktop py-3 border-t border-slate-gray/10 bg-surface/60 backdrop-blur-md">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-label-sm text-on-surface-variant">Model</span>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                disabled={isBusy}
                className="bg-transparent text-label-md font-label-md text-primary
                           focus:ring-0 border-none p-0 cursor-pointer outline-none"
              >
                <option value="gemini">Gemini</option>
                <option value="gpt">GPT-4o</option>
                <option value="gpt5">GPT-5</option>
              </select>
            </div>

            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                id="chat-input"
                rows={1}
                placeholder={
                  mode === 'interview' && interviewPhase === 'questioning'
                    ? 'Type your answer and press Enter to submit…'
                    : 'Ask about your resume…'
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={inputDisabled}
                className="flex-1 px-4 py-3 rounded-xl border border-outline-variant bg-white resize-none
                           text-body-md outline-none focus:border-electric-indigo focus:ring-1 focus:ring-electric-indigo
                           disabled:opacity-60"
              />
              <button
                id="chat-send-btn"
                onClick={() => (mode === 'interview' ? handleSubmitAnswer() : sendMessage())}
                disabled={inputDisabled || !input.trim()}
                type="button"
                className="bg-electric-indigo text-white p-3 rounded-xl hover:brightness-110
                           active:scale-95 transition-all disabled:opacity-40"
              >
                <span className="material-symbols-outlined text-[20px]">send</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
