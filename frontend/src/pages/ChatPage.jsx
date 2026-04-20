import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiSend, FiMessageCircle, FiAlertTriangle } from 'react-icons/fi';
import api from '../api/axios';
import Navbar from '../components/Navbar';

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

  // Auto-scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleChipClick = (chip) => {
    sendMessage(chip);
  };

  const hasUserSent = messages.some((m) => m.role === 'user');

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
            <p>Resume #{resumeId} · Ask follow-up questions about your AI review</p>
          </div>
        </div>

        {/* Messages Area */}
        <div className="chat-messages" id="chat-messages-area">
          {messages.map((msg, index) => (
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
          ))}

          {/* Typing Indicator */}
          {loading && (
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

        {/* Suggestion Chips — show only before first user message */}
        {!hasUserSent && !loading && (
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

        {/* Input Area */}
        <div className="chat-input-area">
          {/* Model Toggle */}
          <div className="chat-model-toggle">
            <button
              className={`model-btn ${model === 'gemini' ? 'active' : ''}`}
              onClick={() => setModel('gemini')}
              type="button"
              disabled={loading}
            >
              Gemini
            </button>
            <button
              className={`model-btn ${model === 'gpt' ? 'active' : ''}`}
              onClick={() => setModel('gpt')}
              type="button"
              disabled={loading}
            >
              GPT
            </button>
          </div>

          <div className="chat-input-row">
            <textarea
              ref={inputRef}
              id="chat-input"
              className="chat-input"
              placeholder="Ask about your resume..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              rows={1}
            />
            <button
              id="chat-send-btn"
              className="chat-send-btn"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              type="button"
            >
              <FiSend />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
