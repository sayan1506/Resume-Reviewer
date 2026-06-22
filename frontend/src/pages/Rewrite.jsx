import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import Navbar from '../components/Navbar';
import { exportTextToPDF } from '../utils/exportPDF';

export default function Rewrite() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [jobDescription, setJobDescription] = useState('');
  const [selectedModel, setSelectedModel] = useState('gemini');
  const [bullets, setBullets] = useState(null);
  const [decisions, setDecisions] = useState({}); // index -> 'accepted' | 'rejected'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fallbackWarning, setFallbackWarning] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setBullets(null);
    setDecisions({});
    setFallbackWarning('');

    try {
      const response = await api.post('/ai/rewrite', {
        resume_id: parseInt(resumeId),
        job_description: jobDescription.trim() || null,
        model: selectedModel,
      });
      setBullets(response.data.bullets || []);
      setFallbackWarning(response.data.fallback_warning || '');
    } catch (err) {
      const status = err.response?.status;
      if (status === 429) {
        setError('Rate limit reached (10/hour). Please wait before trying again.');
      } else {
        setError(err.response?.data?.detail || 'Rewrite failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const setDecision = (i, value) => {
    setDecisions((prev) => ({ ...prev, [i]: prev[i] === value ? undefined : value }));
  };

  const acceptedText = useMemo(() => {
    if (!bullets) return '';
    return bullets
      .filter((_, i) => decisions[i] === 'accepted')
      .map((b) => `• ${b.improved}`)
      .join('\n');
  }, [bullets, decisions]);

  const acceptedCount = useMemo(
    () => Object.values(decisions).filter((d) => d === 'accepted').length,
    [decisions]
  );

  const handleExportPDF = () => {
    exportTextToPDF(acceptedText, `improved-bullets-${resumeId}.pdf`);
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
          <h1 className="font-display text-headline-lg text-on-surface">Resume Bullet Rewriting</h1>
          <p className="mt-1 text-body-md text-on-surface-variant">
            Turn weak bullets into strong, quantified, STAR-formatted versions. Accept the ones you like and export.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6">
          <label htmlFor="jobDescription" className="block mb-1.5 text-label-md text-on-surface-variant">
            Target Job Description <span className="opacity-60">(optional)</span>
          </label>
          <textarea
            id="jobDescription"
            placeholder="Paste a job description to tailor the rewrites (optional)..."
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
                  Rewriting...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[20px]">auto_fix_high</span>
                  {bullets ? 'Rewrite Again' : 'Rewrite Bullets'}
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
            <p className="text-body-md text-on-surface-variant">Rewriting your bullet points...</p>
          </div>
        )}

        {bullets && !loading && bullets.length === 0 && (
          <div className="mt-8 tonal-card rounded-2xl p-6 text-center text-body-md text-on-surface-variant">
            No weak bullets were flagged — your bullet points already look strong.
          </div>
        )}

        {bullets && !loading && bullets.length > 0 && (
          <div className="mt-8 space-y-6">
            {bullets.map((b, i) => {
              const decision = decisions[i];
              return (
                <div
                  key={i}
                  className={`tonal-card rounded-2xl p-6 border transition-colors
                              ${decision === 'accepted' ? 'border-success-teal/40'
                                : decision === 'rejected' ? 'border-error-crimson/30 opacity-60'
                                : 'border-transparent'}`}
                >
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-label-sm font-semibold text-on-surface-variant mb-1">Before</p>
                      <p className="text-body-md text-on-surface-variant line-through decoration-error-crimson/40">
                        {b.original}
                      </p>
                    </div>
                    <div>
                      <p className="text-label-sm font-semibold text-success-teal mb-1">After</p>
                      <p className="text-body-md text-on-surface font-medium">{b.improved}</p>
                    </div>
                  </div>

                  <div className="mt-3 flex items-start gap-2 text-label-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px] text-warning-amber">lightbulb</span>
                    {b.rationale}
                  </div>

                  <div className="mt-4 flex items-center gap-2">
                    <button
                      onClick={() => setDecision(i, 'accepted')}
                      className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-label-md transition-all
                                  ${decision === 'accepted'
                                    ? 'bg-success-teal text-white'
                                    : 'border border-outline-variant text-on-surface-variant hover:bg-surface-container-low'}`}
                    >
                      <span className="material-symbols-outlined text-[18px]">check</span>
                      Accept
                    </button>
                    <button
                      onClick={() => setDecision(i, 'rejected')}
                      className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-label-md transition-all
                                  ${decision === 'rejected'
                                    ? 'bg-error-crimson text-white'
                                    : 'border border-outline-variant text-on-surface-variant hover:bg-surface-container-low'}`}
                    >
                      <span className="material-symbols-outlined text-[18px]">close</span>
                      Reject
                    </button>
                  </div>
                </div>
              );
            })}

            {/* Assemble accepted rewrites */}
            <div className="tonal-card rounded-2xl p-6">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-electric-indigo">playlist_add_check</span>
                  <h2 className="text-headline-md font-display text-on-surface">
                    Accepted Bullets ({acceptedCount})
                  </h2>
                </div>
                <button
                  onClick={handleExportPDF}
                  disabled={acceptedCount === 0}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-outline-variant
                             text-on-surface-variant hover:bg-surface-container-low transition-all text-label-md
                             disabled:opacity-50"
                >
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  Export PDF
                </button>
              </div>
              {acceptedCount > 0 ? (
                <pre className="whitespace-pre-wrap text-body-md text-on-surface font-sans leading-relaxed">
                  {acceptedText}
                </pre>
              ) : (
                <p className="text-body-md text-on-surface-variant">
                  Accept rewrites above to assemble your improved bullet list here.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
