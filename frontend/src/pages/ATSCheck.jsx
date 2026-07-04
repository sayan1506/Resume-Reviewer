import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import Navbar from '../components/Navbar';
import { exportToPDF } from '../utils/exportPDF';

const statusMeta = {
  pass: { icon: 'check_circle', cls: 'text-success-teal', badge: 'bg-success-teal/10 text-success-teal border-success-teal/20' },
  warn: { icon: 'warning', cls: 'text-warning-amber', badge: 'bg-warning-amber/10 text-warning-amber border-warning-amber/20' },
  fail: { icon: 'cancel', cls: 'text-error-crimson', badge: 'bg-error-crimson/10 text-error-crimson border-error-crimson/20' },
};

export default function ATSCheck() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [jobDescription, setJobDescription] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fallbackWarning, setFallbackWarning] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    setFallbackWarning('');

    try {
      const response = await api.post('/ai/ats-check', {
        resume_id: parseInt(resumeId),
        job_description: jobDescription.trim() || null,
        model: selectedModel,
      });
      setResult(response.data);
      setFallbackWarning(response.data.fallback_warning || '');
    } catch (err) {
      const status = err.response?.status;
      if (status === 429) {
        setError('Rate limit reached (10/hour). Please wait before checking again.');
      } else {
        setError(err.response?.data?.detail || 'ATS check failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = () => {
    exportToPDF('ats-report-content', `ats-check-${resumeId}.pdf`);
  };

  return (
    <>
      <Navbar />
      <div className="max-w-3xl mx-auto px-margin-mobile sm:px-margin-desktop py-stack-lg">
        <button
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-2 text-slate-gray hover:text-primary
                     transition-colors mb-6 text-label-md"
        >
          <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          Back to Dashboard
        </button>

        <div>
          <h1 className="font-display text-headline-lg text-on-surface">ATS Compatibility Check</h1>
          <p className="mt-1 text-body-md text-on-surface-variant">
            See how well your resume survives Applicant Tracking Systems. Add a job description for keyword-gap analysis.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6">
          <label htmlFor="jobDescription" className="block mb-1.5 text-label-md text-on-surface-variant">
            Job Description <span className="opacity-60">(optional)</span>
          </label>
          <textarea
            id="jobDescription"
            placeholder="Paste a job description to check keyword overlap (optional)..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            className="w-full p-4 rounded-xl border border-outline-variant bg-white
                       focus:border-electric-indigo focus:ring-1 focus:ring-electric-indigo
                       outline-none resize-none text-body-md min-h-[120px]"
          />

          <div className="mt-4 flex items-center gap-4 flex-wrap">
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
          </div>

          {fallbackWarning && (
            <div className="mt-4 flex items-center gap-2 px-4 py-3 rounded-lg bg-warning-amber/10
                            border border-warning-amber/20 text-warning-amber text-label-md">
              <span className="material-symbols-outlined text-[20px]">warning</span>
              {fallbackWarning}
            </div>
          )}

          <div className="mt-4 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="bg-electric-indigo text-white px-6 py-3 rounded-xl text-label-md font-label-md
                         flex items-center gap-2 hover:shadow-lg hover:shadow-electric-indigo/20
                         active:scale-95 transition-all disabled:opacity-60"
            >
              {loading ? (
                <>
                  <div className="w-[18px] h-[18px] border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Checking...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[20px]">fact_check</span>
                  {result ? 'Re-check' : 'Run ATS Check'}
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-6 flex items-center gap-2 px-4 py-3 rounded-lg bg-error-crimson/10
                          border border-error-crimson/20 text-error-crimson text-label-md">
            <span className="material-symbols-outlined text-[20px]">error</span>
            {error}
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="w-10 h-10 border-4 border-electric-indigo/20 border-t-electric-indigo rounded-full animate-spin" />
            <p className="text-body-md text-on-surface-variant">Analyzing ATS compatibility...</p>
          </div>
        )}

        {result && !loading && (
          <div id="ats-report-content" className="mt-8 space-y-6">
            {/* Parseability gauge */}
            <div className="tonal-card rounded-2xl p-8 flex flex-col items-center">
              {(() => {
                const score = result.parseabilityScore;
                const offset = 552.92 * (1 - score / 100);
                const colorClass = score >= 71 ? 'text-success-teal'
                  : score >= 41 ? 'text-warning-amber'
                  : 'text-error-crimson';
                return (
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
                      <span className="text-label-sm text-on-surface-variant">PARSEABILITY</span>
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Checklist */}
            <div className="tonal-card rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-electric-indigo">checklist</span>
                <h2 className="text-headline-md font-display text-on-surface">Compatibility Checks</h2>
              </div>
              <div className="space-y-3">
                {result.checks.map((c, i) => {
                  const meta = statusMeta[c.status] || statusMeta.warn;
                  return (
                    <div key={i} className="flex items-start gap-3 rounded-xl border border-outline-variant p-4">
                      <span className={`material-symbols-outlined ${meta.cls}`}>{meta.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-body-md font-semibold text-on-surface">{c.label}</p>
                          <span className={`text-label-sm px-2 py-0.5 rounded-full border ${meta.badge}`}>
                            {c.status.toUpperCase()}
                          </span>
                        </div>
                        <p className="mt-1 text-body-md text-on-surface-variant">{c.detail}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Keyword gaps (only when a JD was supplied) */}
            {(result.matchedKeywords?.length > 0 || result.missingKeywords?.length > 0) && (
              <div className="tonal-card rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-electric-indigo">key</span>
                  <h2 className="text-headline-md font-display text-on-surface">Keyword Match vs. Job Description</h2>
                </div>
                {result.matchedKeywords?.length > 0 && (
                  <div className="mb-4">
                    <p className="text-label-md font-semibold text-success-teal mb-2">Matched</p>
                    <div className="flex flex-wrap gap-2">
                      {result.matchedKeywords.map((k, i) => (
                        <span key={i} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full border text-label-sm
                                                  bg-success-teal/10 text-success-teal border-success-teal/20">
                          <span className="material-symbols-outlined text-[16px]">check</span>{k}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {result.missingKeywords?.length > 0 && (
                  <div>
                    <p className="text-label-md font-semibold text-error-crimson mb-2">Missing</p>
                    <div className="flex flex-wrap gap-2">
                      {result.missingKeywords.map((k, i) => (
                        <span key={i} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full border text-label-sm
                                                  bg-error-crimson/10 text-error-crimson border-error-crimson/20">
                          <span className="material-symbols-outlined text-[16px]">close</span>{k}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="flex flex-wrap items-center justify-center gap-3">
              <button
                onClick={handleExportPDF}
                className="bg-white text-primary border border-outline-variant px-6 py-3 rounded-xl
                           text-label-md font-label-md flex items-center gap-2
                           hover:bg-surface-container-low transition-all"
              >
                <span className="material-symbols-outlined text-[20px]">download</span>
                Download PDF
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
