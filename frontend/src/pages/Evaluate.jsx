import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import Navbar from '../components/Navbar';
import ShareModal from '../components/ShareModal';
import { exportToPDF } from '../utils/exportPDF';

const severityClass = {
  high:   'bg-error-crimson/10 text-error-crimson border-error-crimson/20',
  medium: 'bg-warning-amber/10 text-warning-amber border-warning-amber/20',
  low:    'bg-slate-100 text-slate-gray border-slate-gray/20',
};

export default function Evaluate() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [jobDescription, setJobDescription] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt');
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
        <div>
          <h1 className="font-display text-headline-lg text-on-surface">Job Match Evaluation</h1>
          <p className="mt-1 text-body-md text-on-surface-variant">
            Compare your resume against a specific job description
          </p>
        </div>

        {/* Job Description Form */}
        <form onSubmit={handleSubmit} className="mt-6">
          <label htmlFor="jobDescription" className="block mb-1.5 text-label-md text-on-surface-variant">
            Job Description
          </label>
          <textarea
            id="jobDescription"
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            required
            className="w-full p-4 rounded-xl border border-outline-variant bg-white
                       focus:border-electric-indigo focus:ring-1 focus:ring-electric-indigo
                       outline-none resize-none text-body-md min-h-[160px]"
          />

          {/* Model Selector */}
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
              disabled={loading || !jobDescription.trim()}
              className="bg-electric-indigo text-white px-6 py-3 rounded-xl text-label-md font-label-md
                         flex items-center gap-2 hover:shadow-lg hover:shadow-electric-indigo/20
                         active:scale-95 transition-all disabled:opacity-60"
            >
              {loading ? (
                <>
                  <div className="w-[18px] h-[18px] border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[20px]">send</span>
                  Evaluate
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
            <p className="text-body-md text-on-surface-variant">Generating your interview preparation report...</p>
          </div>
        )}

        {result && (
          <div id="evaluate-report-content" className="mt-8 space-y-6">
            {result.title && (
              <h2 className="font-display text-headline-md text-on-surface text-center">{result.title}</h2>
            )}

            {/* Match Score gauge */}
            <div className="tonal-card rounded-2xl p-8 flex flex-col items-center">
              {(() => {
                const score = result.matchScore;
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
                        <span className="text-label-sm text-on-surface-variant">JOB MATCH SCORE</span>
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>

            {/* Technical Questions */}
            {result.technicalQuestions?.length > 0 && (
              <div className="tonal-card rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-electric-indigo">code</span>
                  <h2 className="text-headline-md font-display text-on-surface">Technical Questions</h2>
                </div>
                <div className="space-y-4">
                  {result.technicalQuestions.map((q, i) => (
                    <div key={i} className="rounded-xl border border-outline-variant p-4">
                      <p className="text-label-sm text-electric-indigo font-semibold">Question {i + 1}</p>
                      <p className="mt-1 text-body-md font-semibold text-on-surface">{q.question}</p>
                      <div className="mt-3">
                        <p className="text-label-sm font-semibold text-on-surface-variant">Interviewer Intent:</p>
                        <p className="text-body-md text-on-surface-variant">{q.intention}</p>
                      </div>
                      <p className="mt-3 text-label-sm font-semibold text-on-surface-variant">Strategic Answer Guide:</p>
                      <p className="text-body-md text-on-surface-variant">{q.answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Behavioral Questions */}
            {result.behavioralQuestions?.length > 0 && (
              <div className="tonal-card rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-secondary">groups</span>
                  <h2 className="text-headline-md font-display text-on-surface">Behavioral Questions</h2>
                </div>
                <div className="space-y-4">
                  {result.behavioralQuestions.map((q, i) => (
                    <div key={i} className="rounded-xl border border-outline-variant p-4">
                      <p className="text-label-sm text-secondary font-semibold">Question {i + 1}</p>
                      <p className="mt-1 text-body-md font-semibold text-on-surface">{q.question}</p>
                      <div className="mt-3">
                        <p className="text-label-sm font-semibold text-on-surface-variant">Interviewer Intent:</p>
                        <p className="text-body-md text-on-surface-variant">{q.intention}</p>
                      </div>
                      <p className="mt-3 text-label-sm font-semibold text-on-surface-variant">Strategic Answer Guide:</p>
                      <p className="text-body-md text-on-surface-variant">{q.answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skill Gaps */}
            {result.skillGaps?.length > 0 && (
              <div className="tonal-card rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-warning-amber">warning</span>
                  <h2 className="text-headline-md font-display text-on-surface">Skill Gaps</h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.skillGaps.map((gap, i) => (
                    <span
                      key={i}
                      className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full border text-label-sm
                                  ${severityClass[gap.severity] || severityClass.low}`}
                    >
                      {gap.skill}
                      <span className="opacity-70">({gap.severity})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Preparation Plan */}
            {result.preparationPlan?.length > 0 && (
              <div className="tonal-card rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-electric-indigo">calendar_month</span>
                  <h2 className="text-headline-md font-display text-on-surface">Preparation Plan</h2>
                </div>
                <div className="space-y-4">
                  {result.preparationPlan.map((day, i) => (
                    <div key={i} className="flex gap-4">
                      <div className="flex-shrink-0 w-16 text-label-md font-semibold text-electric-indigo">
                        Day {day.day}
                      </div>
                      <div className="flex-1">
                        <p className="text-body-md font-semibold text-on-surface">{day.focus}</p>
                        <ul className="mt-2 space-y-1">
                          {day.tasks.map((task, j) => (
                            <li key={j} className="flex items-start gap-2 text-body-md text-on-surface-variant">
                              <span className="material-symbols-outlined text-[18px] text-success-teal">check</span>
                              {task}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Share and PDF export buttons */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              <button
                onClick={handleShare}
                disabled={shareLoading || !result}
                className="bg-white text-primary border border-outline-variant px-6 py-3 rounded-xl
                           text-label-md font-label-md flex items-center gap-2
                           hover:bg-surface-container-low transition-all disabled:opacity-60"
              >
                <span className="material-symbols-outlined text-[20px]">share</span>
                {shareLoading ? 'Generating...' : 'Share Report'}
              </button>
              <button
                onClick={handleExportPDF}
                disabled={!result}
                className="bg-white text-primary border border-outline-variant px-6 py-3 rounded-xl
                           text-label-md font-label-md flex items-center gap-2
                           hover:bg-surface-container-low transition-all disabled:opacity-60"
              >
                <span className="material-symbols-outlined text-[20px]">download</span>
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
