import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/axios';
import { exportToPDF } from '../utils/exportPDF';

const severityClass = {
  high:   'bg-error-crimson/10 text-error-crimson border-error-crimson/20',
  medium: 'bg-warning-amber/10 text-warning-amber border-warning-amber/20',
  low:    'bg-slate-100 text-slate-gray border-slate-gray/20',
};

function ScoreGauge({ score, label }) {
  const offset = 552.92 * (1 - score / 100);
  const colorClass = score >= 71 ? 'text-success-teal'
    : score >= 41 ? 'text-warning-amber'
    : 'text-error-crimson';
  return (
    <div className="tonal-card rounded-2xl p-8 flex flex-col items-center">
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
          <span className="text-label-sm text-on-surface-variant">{label}</span>
        </div>
      </div>
    </div>
  );
}

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
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 border-4 border-electric-indigo/20 border-t-electric-indigo rounded-full animate-spin" />
        <p className="text-body-md text-on-surface-variant">Loading shared report...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-margin-mobile">
        <p className="text-body-lg text-error-crimson">{error}</p>
      </div>
    );
  }

  const { report_type, payload, created_at } = data;
  const formattedDate = new Date(created_at).toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric'
  });

  const handleExportPDF = () => {
    exportToPDF('shared-report-content', `${report_type}-report.pdf`);
  };

  return (
    <div className="min-h-screen bg-surface">
      {/* Public navbar (no auth required) */}
      <nav className="sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-slate-gray/10">
        <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop h-16 flex items-center">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
              psychology
            </span>
            <span className="font-display font-bold text-on-surface text-lg">Resume Reviewer</span>
          </div>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-margin-mobile sm:px-margin-desktop py-stack-lg">
        {/* header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="font-display text-headline-lg text-on-surface">
              {report_type === 'review' ? 'Resume Review Report' : 'Interview Prep Report'}
            </h1>
            <p className="mt-1 text-body-md text-on-surface-variant">
              Shared report · Generated on {formattedDate}
            </p>
          </div>
          <button
            onClick={handleExportPDF}
            className="bg-white text-primary border border-outline-variant px-6 py-3 rounded-xl
                       text-label-md font-label-md flex items-center gap-2 hover:bg-surface-container-low transition-all"
          >
            <span className="material-symbols-outlined text-[20px]">download</span>
            Download PDF
          </button>
        </div>

        {/* report content */}
        <div id="shared-report-content" className="mt-8 space-y-6">
          {report_type === 'review' && (
            <>
              <ScoreGauge score={payload.score} label="OUT OF 100" />

              <div className="tonal-card rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-success-teal">check_circle</span>
                  <h2 className="text-headline-md font-display text-on-surface">Key Strengths</h2>
                </div>
                <ul className="space-y-3">
                  {payload.strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-3 text-body-md text-on-surface-variant">
                      <span className="material-symbols-outlined text-[20px] text-success-teal">check</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="tonal-card rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-error-crimson">warning</span>
                  <h2 className="text-headline-md font-display text-on-surface">Critical Weaknesses</h2>
                </div>
                <ul className="space-y-3">
                  {payload.weaknesses.map((w, i) => (
                    <li key={i} className="flex items-start gap-3 text-body-md text-on-surface-variant">
                      <span className="material-symbols-outlined text-[20px] text-error-crimson">close</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="tonal-card rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-warning-amber">lightbulb</span>
                  <h2 className="text-headline-md font-display text-on-surface">AI Suggestions</h2>
                </div>
                <ul className="space-y-3">
                  {payload.suggestions.map((s, i) => (
                    <li key={i} className="flex items-start gap-3 text-body-md text-on-surface-variant">
                      <span className="material-symbols-outlined text-[20px] text-warning-amber">trending_up</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}

          {report_type === 'evaluate' && (
            <>
              {payload.title && (
                <h2 className="font-display text-headline-md text-on-surface text-center">{payload.title}</h2>
              )}

              <ScoreGauge score={payload.matchScore} label="JOB MATCH SCORE" />

              {payload.technicalQuestions?.length > 0 && (
                <div className="tonal-card rounded-2xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="material-symbols-outlined text-electric-indigo">code</span>
                    <h2 className="text-headline-md font-display text-on-surface">Technical Questions</h2>
                  </div>
                  <div className="space-y-4">
                    {payload.technicalQuestions.map((q, i) => (
                      <div key={i} className="rounded-xl border border-outline-variant p-4">
                        <p className="text-label-sm text-electric-indigo font-semibold">Question {i + 1}</p>
                        <p className="mt-1 text-body-md font-semibold text-on-surface">{q.question}</p>
                        <p className="mt-3 text-label-sm font-semibold text-on-surface-variant">Interviewer Intent:</p>
                        <p className="text-body-md text-on-surface-variant">{q.intention}</p>
                        <p className="mt-3 text-label-sm font-semibold text-on-surface-variant">Strategic Answer Guide:</p>
                        <p className="text-body-md text-on-surface-variant">{q.answer}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {payload.behavioralQuestions?.length > 0 && (
                <div className="tonal-card rounded-2xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="material-symbols-outlined text-secondary">groups</span>
                    <h2 className="text-headline-md font-display text-on-surface">Behavioral Questions</h2>
                  </div>
                  <div className="space-y-4">
                    {payload.behavioralQuestions.map((q, i) => (
                      <div key={i} className="rounded-xl border border-outline-variant p-4">
                        <p className="text-label-sm text-secondary font-semibold">Question {i + 1}</p>
                        <p className="mt-1 text-body-md font-semibold text-on-surface">{q.question}</p>
                        <p className="mt-3 text-label-sm font-semibold text-on-surface-variant">Interviewer Intent:</p>
                        <p className="text-body-md text-on-surface-variant">{q.intention}</p>
                        <p className="mt-3 text-label-sm font-semibold text-on-surface-variant">Strategic Answer Guide:</p>
                        <p className="text-body-md text-on-surface-variant">{q.answer}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {payload.skillGaps?.length > 0 && (
                <div className="tonal-card rounded-2xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="material-symbols-outlined text-warning-amber">warning</span>
                    <h2 className="text-headline-md font-display text-on-surface">Skill Gaps</h2>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {payload.skillGaps.map((gap, i) => (
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

              {payload.preparationPlan?.length > 0 && (
                <div className="tonal-card rounded-2xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="material-symbols-outlined text-electric-indigo">calendar_month</span>
                    <h2 className="text-headline-md font-display text-on-surface">Preparation Plan</h2>
                  </div>
                  <div className="space-y-4">
                    {payload.preparationPlan.map((day, i) => (
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
            </>
          )}
        </div>

        {/* footer CTA */}
        <div className="mt-12 text-center">
          <p className="text-body-md text-on-surface-variant">Want AI-powered feedback on your own resume?</p>
          <a
            href="https://resume-reviewer-navy.vercel.app/signup"
            className="inline-flex items-center gap-2 mt-3 bg-electric-indigo text-white px-6 py-3 rounded-xl
                       text-label-md font-label-md hover:brightness-110 transition-all no-underline"
          >
            <span className="material-symbols-outlined text-[20px]">rocket_launch</span>
            Try Resume Reviewer Free
          </a>
        </div>
      </div>
    </div>
  );
}
