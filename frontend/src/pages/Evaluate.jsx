import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiArrowLeft,
  FiSend,
  FiCode,
  FiUsers,
  FiAlertTriangle,
  FiCalendar,
  FiShare2,
  FiDownload,
} from 'react-icons/fi';
import api from '../api/axios';
import Navbar from '../components/Navbar';
import ShareModal from '../components/ShareModal';
import { exportToPDF } from '../utils/exportPDF';

export default function Evaluate() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [jobDescription, setJobDescription] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedModel, setSelectedModel] = useState('gemini');
  const [fallbackWarning, setFallbackWarning] = useState('');
  const [shareUrl, setShareUrl] = useState('');
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareLoading, setShareLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jobDescription.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await api.post('/ai/evaluate', {
        resume_id: parseInt(resumeId),
        job_description: jobDescription,
        model: selectedModel,
      });
      setResult(response.data);
      setFallbackWarning(response.data.fallback_warning || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    setShareLoading(true);
    try {
      const response = await api.post('/share/create', result, {
        params: { resume_id: parseInt(resumeId), report_type: 'evaluate' }
      });
      setShareUrl(response.data.share_url);
      setShowShareModal(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate share link');
    } finally {
      setShareLoading(false);
    }
  };

  const handleExportPDF = () => {
    exportToPDF('evaluate-report-content', `interview-report-${resumeId}.pdf`);
  };

  const scoreOffset = result ? 502 - (502 * result.matchScore) / 100 : 502;

  return (
    <>
      <Navbar />
      <div className="results-container">
        <button className="btn-back" onClick={() => navigate('/dashboard')}>
          <FiArrowLeft /> Back to Dashboard
        </button>

        <div className="results-header">
          <h1>Job Match Evaluation</h1>
          <p>Compare your resume against a specific job description</p>
        </div>

        {/* Job Description Form */}
        <div className="evaluate-form-section">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="jobDescription">Job Description</label>
              <textarea
                id="jobDescription"
                className="job-textarea"
                placeholder="Paste the job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                required
              />
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
            </div>

            {fallbackWarning && (
              <div className="fallback-warning">
                ⚠️ {fallbackWarning}
              </div>
            )}

            <div className="form-actions">
              <button type="submit" className="btn-submit" disabled={loading || !jobDescription.trim()}>
                {loading ? (
                  <>
                    <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }}></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <FiSend />
                    Evaluate
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p className="loading-text">Generating your interview preparation report...</p>
          </div>
        )}

        {result && (
          <div id="evaluate-report-content">
            {/* Title */}
            {result.title && (
              <div className="results-header" style={{ marginBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.5rem' }}>{result.title}</h1>
              </div>
            )}

            {/* Match Score */}
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
                <div className="score-value">{result.matchScore}</div>
              </div>
            </div>
            <p className="score-label" style={{ textAlign: 'center', marginBottom: '2rem' }}>
              Job Match Score
            </p>

            {/* Technical Questions */}
            {result.technicalQuestions?.length > 0 && (
              <div className="result-card">
                <h2>
                  <FiCode className="card-icon" style={{ color: 'var(--accent-end)' }} />
                  Technical Questions
                </h2>
                {result.technicalQuestions.map((q, i) => (
                  <div key={i} className="question-card">
                    <h4>Q{i + 1}: {q.question}</h4>
                    <p className="intention">Intent: {q.intention}</p>
                    <p className="answer">{q.answer}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Behavioral Questions */}
            {result.behavioralQuestions?.length > 0 && (
              <div className="result-card">
                <h2>
                  <FiUsers className="card-icon" style={{ color: 'var(--success)' }} />
                  Behavioral Questions
                </h2>
                {result.behavioralQuestions.map((q, i) => (
                  <div key={i} className="question-card">
                    <h4>Q{i + 1}: {q.question}</h4>
                    <p className="intention">Intent: {q.intention}</p>
                    <p className="answer">{q.answer}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Skill Gaps */}
            {result.skillGaps?.length > 0 && (
              <div className="result-card">
                <h2>
                  <FiAlertTriangle className="card-icon" style={{ color: 'var(--warning)' }} />
                  Skill Gaps
                </h2>
                <div className="skill-gaps-grid">
                  {result.skillGaps.map((gap, i) => (
                    <span key={i} className={`skill-badge ${gap.severity}`}>
                      {gap.skill}
                      <span style={{ opacity: 0.7, fontSize: '0.75rem' }}>({gap.severity})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Preparation Plan */}
            {result.preparationPlan?.length > 0 && (
              <div className="result-card">
                <h2>
                  <FiCalendar className="card-icon" style={{ color: 'var(--info)' }} />
                  Preparation Plan
                </h2>
                <div className="prep-timeline">
                  {result.preparationPlan.map((day, i) => (
                    <div key={i} className="prep-day">
                      <h4>Day {day.day}</h4>
                      <p className="focus">{day.focus}</p>
                      <ul>
                        {day.tasks.map((task, j) => (
                          <li key={j}>{task}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Share and PDF export buttons */}
          <div style={{ textAlign: 'center', marginTop: '2rem', display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <button className="btn-action btn-share" onClick={handleShare} disabled={shareLoading || !result}>
              <FiShare2 />
              {shareLoading ? 'Generating...' : 'Share Report'}
            </button>
            <button className="btn-action btn-download" onClick={handleExportPDF} disabled={!result}>
              <FiDownload />
              Download PDF
            </button>
          </div>
          </div>
        )}

        {showShareModal && (
          <ShareModal shareUrl={shareUrl} onClose={() => setShowShareModal(false)} />
        )}
      </div>
    </>
  );
}
