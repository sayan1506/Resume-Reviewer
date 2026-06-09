import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  FiCheckCircle, FiAlertCircle, FiZap,
  FiCode, FiUsers, FiAlertTriangle, FiCalendar, FiDownload
} from 'react-icons/fi';
import api from '../api/axios';
import { exportToPDF } from '../utils/exportPDF';

export default function SharedReportPage() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await api.get(`/share/${token}`);
        setData(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Report not found or link is invalid.');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [token]);

  if (loading) {
    return (
      <div className="results-container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
        <div className="spinner"></div>
        <p className="loading-text">Loading shared report...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
        <p style={{ color: 'var(--error)' }}>{error}</p>
      </div>
    );
  }

  const { report_type, payload, created_at } = data;
  const formattedDate = new Date(created_at).toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric'
  });

  const handleExportPDF = () => {
    exportToPDF(
      'shared-report-content',
      `${report_type}-report.pdf`
    );
  };

  return (
    <div className="results-container">

      {/* Header */}
      <div className="results-header">
        <h1>{report_type === 'review' ? 'Resume Review Report' : 'Interview Prep Report'}</h1>
        <p>Shared report · Generated on {formattedDate}</p>
      </div>

      {/* PDF export */}
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <button className="btn-action btn-download" onClick={handleExportPDF}>
          <FiDownload />
          Download PDF
        </button>
      </div>

      {/* Captured content starts here */}
      <div id="shared-report-content">

        {report_type === 'review' && (
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
                    cx="90" cy="90" r="80"
                    style={{ strokeDashoffset: 502 - (502 * payload.score) / 100 }}
                  />
                </svg>
                <div className="score-value">{payload.score}</div>
              </div>
            </div>
            <p className="score-label" style={{ textAlign: 'center', marginBottom: '2rem' }}>
              Overall Resume Score
            </p>

            <div className="result-card">
              <h2><FiCheckCircle className="card-icon" style={{ color: 'var(--success)' }} /> Strengths</h2>
              <ul className="result-list strengths-list">
                {payload.strengths.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>

            <div className="result-card">
              <h2><FiAlertCircle className="card-icon" style={{ color: 'var(--error)' }} /> Weaknesses</h2>
              <ul className="result-list weaknesses-list">
                {payload.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>

            <div className="result-card">
              <h2><FiZap className="card-icon" style={{ color: 'var(--info)' }} /> Suggestions</h2>
              <ul className="result-list suggestions-list">
                {payload.suggestions.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          </>
        )}

        {report_type === 'evaluate' && (
          <>
            {/* Title */}
            {payload.title && (
              <div className="results-header" style={{ marginBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.5rem' }}>{payload.title}</h1>
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
                    cx="90" cy="90" r="80"
                    style={{ strokeDashoffset: 502 - (502 * payload.matchScore) / 100 }}
                  />
                </svg>
                <div className="score-value">{payload.matchScore}</div>
              </div>
            </div>
            <p className="score-label" style={{ textAlign: 'center', marginBottom: '2rem' }}>
              Job Match Score
            </p>

            {payload.technicalQuestions?.length > 0 && (
              <div className="result-card">
                <h2><FiCode className="card-icon" style={{ color: 'var(--accent-end)' }} /> Technical Questions</h2>
                {payload.technicalQuestions.map((q, i) => (
                  <div key={i} className="question-card">
                    <h4>Q{i + 1}: {q.question}</h4>
                    <p className="intention">Intent: {q.intention}</p>
                    <p className="answer">{q.answer}</p>
                  </div>
                ))}
              </div>
            )}

            {payload.behavioralQuestions?.length > 0 && (
              <div className="result-card">
                <h2><FiUsers className="card-icon" style={{ color: 'var(--success)' }} /> Behavioral Questions</h2>
                {payload.behavioralQuestions.map((q, i) => (
                  <div key={i} className="question-card">
                    <h4>Q{i + 1}: {q.question}</h4>
                    <p className="intention">Intent: {q.intention}</p>
                    <p className="answer">{q.answer}</p>
                  </div>
                ))}
              </div>
            )}

            {payload.skillGaps?.length > 0 && (
              <div className="result-card">
                <h2><FiAlertTriangle className="card-icon" style={{ color: 'var(--warning)' }} /> Skill Gaps</h2>
                <div className="skill-gaps-grid">
                  {payload.skillGaps.map((gap, i) => (
                    <span key={i} className={`skill-badge ${gap.severity}`}>
                      {gap.skill}
                      <span style={{ opacity: 0.7, fontSize: '0.75rem' }}>({gap.severity})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {payload.preparationPlan?.length > 0 && (
              <div className="result-card">
                <h2><FiCalendar className="card-icon" style={{ color: 'var(--info)' }} /> Preparation Plan</h2>
                <div className="prep-timeline">
                  {payload.preparationPlan.map((day, i) => (
                    <div key={i} className="prep-day">
                      <h4>Day {day.day}</h4>
                      <p className="focus">{day.focus}</p>
                      <ul>
                        {day.tasks.map((task, j) => <li key={j}>{task}</li>)}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

      </div>
      {/* End captured content */}

      {/* Footer CTA */}
      <div style={{ textAlign: 'center', marginTop: '3rem', padding: '2rem', opacity: 0.7 }}>
        <p>Want AI-powered feedback on your own resume?</p>
        <a href="https://resume-reviewer-navy.vercel.app/signup" className="btn-action btn-review"
           style={{ display: 'inline-flex', marginTop: '0.75rem', textDecoration: 'none' }}>
          Try Resume Reviewer
        </a>
      </div>
    </div>
  );
}
