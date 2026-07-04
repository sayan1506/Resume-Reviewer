import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import Navbar from '../components/Navbar';
import ShareModal from '../components/ShareModal';
import ScoreTrend from '../components/ScoreTrend';
import { exportToPDF } from '../utils/exportPDF';

export default function ReviewResults() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt');
  const [fallbackWarning, setFallbackWarning] = useState('');
  const [shareUrl, setShareUrl] = useState('');
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareLoading, setShareLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const fetchHistory = useCallback(async () => {
    try {
      const response = await api.get(`/resume/${parseInt(resumeId)}/history`);
      setHistory(Array.isArray(response.data) ? response.data : []);
    } catch {
      // Trend is non-critical; leave history empty on failure.
      setHistory([]);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const fetchReview = async () => {
    try {
      const response = await api.post('/ai/review', {
        resume_id: parseInt(resumeId),
        model: selectedModel,
      });
      setResult(response.data);
      setFallbackWarning(response.data.fallback_warning || '');
      fetchHistory();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch review');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    setShareLoading(true);
    try {
      const response = await api.post('/share/create', null, {
        params: { resume_id: parseInt(resumeId), report_type: 'review' }
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
    exportToPDF('review-report-content', `resume-review-${resumeId}.pdf`);
  };

  return (
    <>
      <Navbar />
      <div className="max-w-3xl mx-auto px-margin-mobile sm:px-margin-desktop py-stack-lg">
        {/* back button */}
        <button
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-2 text-slate-gray hover:text-primary
                     transition-colors mb-6 text-label-md"
        >
          <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          Back to Dashboard
        </button>

        {/* page header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="font-display text-headline-lg text-on-surface">Resume Review</h1>
            <p className="mt-1 text-body-md text-on-surface-variant">AI-powered analysis of your resume</p>
          </div>
          {result && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleShare}
                disabled={shareLoading}
                className="w-10 h-10 flex items-center justify-center rounded-lg border border-outline-variant
                           text-on-surface-variant hover:bg-surface-container-low transition-all disabled:opacity-60"
                title="Share"
              >
                <span className="material-symbols-outlined text-[20px]">share</span>
              </button>
              <button
                onClick={handleExportPDF}
                className="w-10 h-10 flex items-center justify-center rounded-lg border border-outline-variant
                           text-on-surface-variant hover:bg-surface-container-low transition-all"
                title="Download PDF"
              >
                <span className="material-symbols-outlined text-[20px]">download</span>
              </button>
            </div>
          )}
        </div>

        {/* model selector + run button */}
        <div className="mt-6 flex items-center gap-4 flex-wrap">
          <span className="text-label-md text-on-surface-variant">AI Model</span>
          <div className="inline-flex rounded-lg border border-outline-variant overflow-hidden">
            <button
              onClick={() => setSelectedModel('gemini')}
              type="button"
              className={`px-4 py-1.5 text-label-md font-label-md transition-colors
                          ${selectedModel === 'gemini' ? 'bg-electric-indigo text-white' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
            >
              Gemini
            </button>
            <button
              onClick={() => setSelectedModel('gpt')}
              type="button"
              className={`px-4 py-1.5 text-label-md font-label-md transition-colors
                          ${selectedModel === 'gpt' ? 'bg-electric-indigo text-white' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
            >
              GPT-4o
            </button>
            <button
              onClick={() => setSelectedModel('gpt5')}
              type="button"
              className={`px-4 py-1.5 text-label-md font-label-md transition-colors
                          ${selectedModel === 'gpt5' ? 'bg-electric-indigo text-white' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
            >
              GPT-5
            </button>
          </div>
          <button
            onClick={() => { setLoading(true); setResult(null); setError(''); fetchReview(); }}
            disabled={loading}
            className="bg-primary text-on-primary px-6 py-2.5 rounded-lg text-label-md
                       font-label-md flex items-center gap-2 hover:bg-primary-container
                       transition-all active:scale-95 disabled:opacity-60"
          >
            <span className="material-symbols-outlined text-[20px]">refresh</span>
            {result ? 'Re-Review' : 'Run Review'}
          </button>
        </div>

        {/* fallback warning */}
        {fallbackWarning && (
          <div className="mt-6 flex items-center gap-2 px-4 py-3 rounded-lg bg-warning-amber/10
                          border border-warning-amber/20 text-warning-amber text-label-md">
            <span className="material-symbols-outlined text-[20px]">warning</span>
            {fallbackWarning}
          </div>
        )}

        {/* error */}
        {error && (
          <div className="mt-6 flex items-center gap-2 px-4 py-3 rounded-lg bg-error-crimson/10
                          border border-error-crimson/20 text-error-crimson text-label-md">
            <span className="material-symbols-outlined text-[20px]">error</span>
            {error}
          </div>
        )}

        {/* loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="w-10 h-10 border-4 border-electric-indigo/20 border-t-electric-indigo rounded-full animate-spin" />
            <p className="text-body-md text-on-surface-variant">Analyzing your resume with AI...</p>
          </div>
        )}

        {/* score trend across all reviews (outside the PDF export container) */}
        {history.length >= 2 && (
          <div className="mt-8">
            <ScoreTrend history={history} />
          </div>
        )}

        {/* ── Results ─────────────────────────────────────── */}
        {result && (
          <div id="review-report-content" className="mt-8 space-y-6">
            {/* score gauge card */}
            <div className="tonal-card rounded-2xl p-8 flex flex-col items-center">
              {(() => {
                const score = result.score;
                const offset = 552.92 * (1 - score / 100);
                const colorClass = score >= 71 ? 'text-success-teal'
                  : score >= 41 ? 'text-warning-amber'
                  : 'text-error-crimson';
                return (
                  <>
                    <div className="relative w-48 h-48">
                      <svg className="w-full h-full -rotate-90" viewBox="0 0 192 192">
                        <circle cx="96" cy="96" r="88" fill="none" stroke="#e2e7ff" strokeWidth="12" />
                        <circle
                          cx="96" cy="96" r="88" fill="none" stroke="currentColor" strokeWidth="12"
                          strokeLinecap="round" strokeDasharray="552.92" strokeDashoffset={offset}
                          className={colorClass}
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-headline-lg font-display text-on-surface">{score}</span>
                        <span className="text-label-sm text-on-surface-variant">OUT OF 100</span>
                      </div>
                    </div>
                    <p className="mt-4 text-headline-md font-display text-on-surface">Overall Resume Score</p>
                  </>
                );
              })()}
            </div>

            {/* strengths card */}
            <div className="tonal-card rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-success-teal">check_circle</span>
                <h2 className="text-headline-md font-display text-on-surface">Key Strengths</h2>
              </div>
              <ul className="space-y-3">
                {result.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-[20px] text-success-teal">check</span>
                    <span className="text-body-md text-on-surface-variant">{s}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* weaknesses card */}
            <div className="tonal-card rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-error-crimson">warning</span>
                <h2 className="text-headline-md font-display text-on-surface">Critical Weaknesses</h2>
              </div>
              <ul className="space-y-3">
                {result.weaknesses.map((w, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-[20px] text-error-crimson">close</span>
                    <span className="text-body-md text-on-surface-variant">{w}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* suggestions card */}
            <div className="tonal-card rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-warning-amber">lightbulb</span>
                <h2 className="text-headline-md font-display text-on-surface">AI Suggestions</h2>
              </div>
              <ul className="space-y-3">
                {result.suggestions.map((s, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-[20px] text-warning-amber">trending_up</span>
                    <span className="text-body-md text-on-surface-variant">{s}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* bottom action buttons */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => navigate(`/evaluate/${resumeId}`)}
                  className="bg-electric-indigo text-white px-6 py-3 rounded-xl text-label-md font-label-md
                             flex items-center gap-2 hover:shadow-lg hover:shadow-electric-indigo/20
                             active:scale-95 transition-all"
                >
                  <span className="material-symbols-outlined text-[20px]">search_check</span>
                  Evaluate Against Job
                </button>
                <button
                  onClick={() => navigate(`/chat/${resumeId}`)}
                  className="bg-white text-primary border border-outline-variant px-6 py-3 rounded-xl
                             text-label-md font-label-md flex items-center gap-2
                             hover:bg-surface-container-low transition-all"
                >
                  <span className="material-symbols-outlined text-[20px]">chat</span>
                  Chat with AI
                </button>
                <button
                  onClick={() => navigate(`/cover-letter/${resumeId}`)}
                  className="bg-white text-primary border border-outline-variant px-6 py-3 rounded-xl
                             text-label-md font-label-md flex items-center gap-2
                             hover:bg-surface-container-low transition-all"
                >
                  <span className="material-symbols-outlined text-[20px]">edit_note</span>
                  Cover Letter
                </button>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleShare}
                  disabled={shareLoading}
                  className="w-11 h-11 flex items-center justify-center rounded-xl border border-outline-variant
                             text-on-surface-variant hover:bg-surface-container-low transition-all disabled:opacity-60"
                  title="Share"
                >
                  <span className="material-symbols-outlined text-[20px]">share</span>
                </button>
                <button
                  onClick={handleExportPDF}
                  className="bg-white text-primary border border-outline-variant px-6 py-3 rounded-xl
                             text-label-md font-label-md flex items-center gap-2 hover:bg-surface-container-low transition-all"
                >
                  <span className="material-symbols-outlined text-[20px]">download</span>
                  Download PDF
                </button>
              </div>
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
