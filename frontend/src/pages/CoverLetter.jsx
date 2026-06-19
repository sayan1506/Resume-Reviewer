import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import Navbar from '../components/Navbar';
import { exportTextToPDF } from '../utils/exportPDF';

const TONES = [
  { value: 'professional', label: 'Professional' },
  { value: 'enthusiastic', label: 'Enthusiastic' },
  { value: 'concise', label: 'Concise' },
];

export default function CoverLetter() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [jobDescription, setJobDescription] = useState('');
  const [tone, setTone] = useState('professional');
  const [selectedModel, setSelectedModel] = useState('gemini');
  const [letter, setLetter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fallbackWarning, setFallbackWarning] = useState('');
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jobDescription.trim()) return;

    setLoading(true);
    setError('');
    setLetter('');
    setFallbackWarning('');

    try {
      const response = await api.post('/ai/cover-letter', {
        resume_id: parseInt(resumeId),
        job_description: jobDescription,
        tone,
        model: selectedModel,
      });
      setLetter(response.data.cover_letter || '');
      setFallbackWarning(response.data.fallback_warning || '');
    } catch (err) {
      const status = err.response?.status;
      if (status === 429) {
        setError('Rate limit reached (10/hour). Please wait before generating another.');
      } else {
        setError(err.response?.data?.detail || 'Failed to generate cover letter');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = () => {
    exportTextToPDF(letter, `cover-letter-${resumeId}.pdf`);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(letter);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Could not copy to clipboard.');
    }
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
          <h1 className="font-display text-headline-lg text-on-surface">Cover Letter Generator</h1>
          <p className="mt-1 text-body-md text-on-surface-variant">
            Generate a tailored cover letter from your resume and a job description
          </p>
        </div>

        {/* form */}
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

          <div className="mt-4 flex items-center gap-4 flex-wrap">
            <span className="text-label-md text-on-surface-variant">Tone</span>
            <div className="inline-flex rounded-lg border border-outline-variant overflow-hidden">
              {TONES.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTone(t.value)}
                  type="button"
                  className={`px-4 py-1.5 text-label-md font-label-md transition-colors
                              ${tone === t.value ? 'bg-electric-indigo text-white' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

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
              disabled={loading || !jobDescription.trim()}
              className="bg-electric-indigo text-white px-6 py-3 rounded-xl text-label-md font-label-md
                         flex items-center gap-2 hover:shadow-lg hover:shadow-electric-indigo/20
                         active:scale-95 transition-all disabled:opacity-60"
            >
              {loading ? (
                <>
                  <div className="w-[18px] h-[18px] border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Writing...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[20px]">edit_note</span>
                  {letter ? 'Regenerate' : 'Generate Cover Letter'}
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
            <p className="text-body-md text-on-surface-variant">Drafting your cover letter...</p>
          </div>
        )}

        {letter && !loading && (
          <div className="mt-8">
            <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-electric-indigo">description</span>
                <h2 className="text-headline-md font-display text-on-surface">Your Cover Letter</h2>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-outline-variant
                             text-on-surface-variant hover:bg-surface-container-low transition-all text-label-md"
                >
                  <span className="material-symbols-outlined text-[18px]">{copied ? 'check' : 'content_copy'}</span>
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  onClick={handleExportPDF}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-outline-variant
                             text-on-surface-variant hover:bg-surface-container-low transition-all text-label-md"
                >
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  PDF
                </button>
              </div>
            </div>
            <p className="mb-2 text-label-sm text-on-surface-variant">
              Edit freely below — the PDF and copy use your edited text.
            </p>
            <textarea
              value={letter}
              onChange={(e) => setLetter(e.target.value)}
              className="w-full p-5 rounded-xl border border-outline-variant bg-white
                         focus:border-electric-indigo focus:ring-1 focus:ring-electric-indigo
                         outline-none resize-y text-body-md min-h-[420px] leading-relaxed whitespace-pre-wrap"
            />
          </div>
        )}
      </div>
    </>
  );
}
