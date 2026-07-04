import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import Navbar from '../components/Navbar';

function matchColor(pct) {
  return pct >= 71 ? 'text-success-teal' : pct >= 41 ? 'text-warning-amber' : 'text-error-crimson';
}

export default function JobMatch() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt');
  const [jobs, setJobs] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fallbackWarning, setFallbackWarning] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setJobs(null);
    setFallbackWarning('');

    try {
      const response = await api.post('/ai/job-match', {
        resume_id: parseInt(resumeId),
        query: query.trim() || null,
        model: selectedModel,
      });
      setJobs(response.data.jobs || []);
      setFallbackWarning(response.data.fallback_warning || '');
    } catch (err) {
      const status = err.response?.status;
      if (status === 429) {
        setError('Rate limit reached (10/hour). Please wait before searching again.');
      } else if (status === 503) {
        setError('Job sources are temporarily unavailable. Please try again shortly.');
      } else {
        setError(err.response?.data?.detail || 'Job matching failed');
      }
    } finally {
      setLoading(false);
    }
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
          <h1 className="font-display text-headline-lg text-on-surface">Which Jobs Fit Your Resume</h1>
          <p className="mt-1 text-body-md text-on-surface-variant">
            We pull live openings and rank them against your resume. Add a keyword to focus the search.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6">
          <label htmlFor="query" className="block mb-1.5 text-label-md text-on-surface-variant">
            Search keyword <span className="opacity-60">(optional)</span>
          </label>
          <input
            id="query"
            type="text"
            placeholder="e.g. frontend, data analyst, product manager..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full p-4 rounded-xl border border-outline-variant bg-white
                       focus:border-electric-indigo focus:ring-1 focus:ring-electric-indigo
                       outline-none text-body-md"
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
                  Matching...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[20px]">work</span>
                  {jobs ? 'Search Again' : 'Find Matching Jobs'}
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
            <p className="text-body-md text-on-surface-variant">Fetching and ranking live job listings...</p>
          </div>
        )}

        {jobs && !loading && jobs.length === 0 && (
          <div className="mt-8 tonal-card rounded-2xl p-6 text-center text-body-md text-on-surface-variant">
            No matching jobs found. Try a broader keyword.
          </div>
        )}

        {jobs && !loading && jobs.length > 0 && (
          <div className="mt-8 space-y-4">
            {jobs.map((job, i) => (
              <div key={i} className="tonal-card rounded-2xl p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-headline-md font-display text-on-surface">{job.title}</h3>
                    <p className="text-label-md text-on-surface-variant">
                      {job.company} · <span className="opacity-70">{job.source}</span>
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className={`block text-headline-md font-display leading-none ${matchColor(job.matchPct)}`}>
                      {job.matchPct}%
                    </span>
                    <span className="text-label-sm text-on-surface-variant">match</span>
                  </div>
                </div>

                <p className="mt-3 text-body-md text-on-surface-variant">{job.whyFit}</p>

                {job.skillGaps?.length > 0 && (
                  <div className="mt-3">
                    <p className="text-label-sm font-semibold text-on-surface-variant mb-1.5">Skills to strengthen</p>
                    <div className="flex flex-wrap gap-2">
                      {job.skillGaps.map((gap, j) => (
                        <span key={j} className="inline-flex items-center gap-1 px-3 py-1 rounded-full border text-label-sm
                                                  bg-warning-amber/10 text-warning-amber border-warning-amber/20">
                          {gap}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-4">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-electric-indigo text-white
                               text-label-md font-label-md hover:brightness-110 transition-all"
                  >
                    <span className="material-symbols-outlined text-[18px]">open_in_new</span>
                    View &amp; Apply
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
