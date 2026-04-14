import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiCheckCircle, FiAlertCircle, FiZap, FiClipboard } from 'react-icons/fi';
import api from '../api/axios';
import Navbar from '../components/Navbar';

export default function ReviewResults() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedModel, setSelectedModel] = useState('gemini');
  const [fallbackWarning, setFallbackWarning] = useState('');

  const fetchReview = async () => {
    try {
      const response = await api.post('/ai/review', {
        resume_id: parseInt(resumeId),
        model: selectedModel,
      });
      setResult(response.data);
      setFallbackWarning(response.data.fallback_warning || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch review');
    } finally {
      setLoading(false);
    }
  };

  const scoreOffset = result ? 502 - (502 * result.score) / 100 : 502;

  return (
    <>
      <Navbar />
      <div className="results-container">
        <button className="btn-back" onClick={() => navigate('/dashboard')}>
          <FiArrowLeft /> Back to Dashboard
        </button>

        <div className="results-header">
          <h1>Resume Review</h1>
          <p>AI-powered analysis of your resume</p>
        </div>

        {/* Model Selector */}
        <div className="model-selector">
          <label>AI Model:</label>
          <div className="model-toggle">
            <button
              className={`model-btn ${selectedModel === 'gemini' ? 'active' : ''}`}
              onClick={() => setSelectedModel('gemini')}
              type="button"
            >
              Gemini
            </button>
            <button
              className={`model-btn ${selectedModel === 'gpt' ? 'active' : ''}`}
              onClick={() => setSelectedModel('gpt')}
              type="button"
            >
              GPT-4o
            </button>
          </div>
          <button
            className="btn-action btn-review"
            onClick={() => { setLoading(true); setResult(null); setError(''); fetchReview(); }}
            type="button"
            disabled={loading}
          >
            {result ? 'Re-Review' : 'Run Review'}
          </button>
        </div>

        {fallbackWarning && (
          <div className="fallback-warning">
            ⚠️ {fallbackWarning}
          </div>
        )}

        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p className="loading-text">Analyzing your resume with AI...</p>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}

        {result && (
          <>
            {/* Score Gauge */}
            <div className="score-section">
              <div className="score-gauge">
                <svg viewBox="0 0 180 180">
                  <defs>
                    <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#6366f1" />
                      <stop offset="50%" stopColor="#8b5cf6" />
                      <stop offset="100%" stopColor="#a78bfa" />
                    </linearGradient>
                  </defs>
                  <circle className="bg-circle" cx="90" cy="90" r="80" />
                  <circle
                    className="progress-circle"
                    cx="90"
                    cy="90"
                    r="80"
                    style={{ strokeDashoffset: scoreOffset }}
                  />
                </svg>
                <div className="score-value">{result.score}</div>
              </div>
            </div>
            <p className="score-label" style={{ textAlign: 'center', marginBottom: '2rem' }}>
              Overall Resume Score
            </p>

            {/* Strengths */}
            <div className="result-card" style={{ animationDelay: '0.1s' }}>
              <h2>
                <FiCheckCircle className="card-icon" style={{ color: 'var(--success)' }} />
                Strengths
              </h2>
              <ul className="result-list strengths-list">
                {result.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>

            {/* Weaknesses */}
            <div className="result-card" style={{ animationDelay: '0.2s' }}>
              <h2>
                <FiAlertCircle className="card-icon" style={{ color: 'var(--error)' }} />
                Weaknesses
              </h2>
              <ul className="result-list weaknesses-list">
                {result.weaknesses.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>

            {/* Suggestions */}
            <div className="result-card" style={{ animationDelay: '0.3s' }}>
              <h2>
                <FiZap className="card-icon" style={{ color: 'var(--info)' }} />
                Suggestions
              </h2>
              <ul className="result-list suggestions-list">
                {result.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>

            {/* Navigate to Evaluate */}
            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
              <button
                className="btn-action btn-evaluate"
                onClick={() => navigate(`/evaluate/${resumeId}`)}
                style={{ padding: '0.85rem 2.5rem', fontSize: '1rem', width: 'auto', display: 'inline-flex' }}
              >
                <FiClipboard />
                Evaluate Against a Job
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
