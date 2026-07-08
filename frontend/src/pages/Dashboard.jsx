import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import api from '../api/axios';
import Navbar from '../components/Navbar';
import ResumeViewerModal from '../components/ResumeViewerModal';

export default function Dashboard() {
  const [resumes, setResumes] = useState([]);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [expandedCards, setExpandedCards] = useState({});
  const [viewingResume, setViewingResume] = useState(null);
  const navigate = useNavigate();

  const toggleExpand = (id) => {
    setExpandedCards((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Fetch resume history on mount
  useEffect(() => {
    const fetchResumes = async () => {
      try {
        const response = await api.get('/resume/list');
        setResumes(
          response.data.map((r) => ({
            id: r.id,
            fileUrl: r.file_url,
            fileName: `Resume #${r.id}`,
            uploadedAt: r.uploaded_at
              ? new Date(r.uploaded_at).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })
              : 'Unknown',
            hasAnalysis: r.has_analysis,
            score: r.score,
            strengths: r.strengths,
            weaknesses: r.weaknesses,
            suggestions: r.suggestions,
          }))
        );
      } catch (err) {
        console.error('Failed to fetch resumes:', err);
      } finally {
        setLoadingHistory(false);
      }
    };

    fetchResumes();
  }, []);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setUploadStatus({ type: 'error', message: 'Only PDF files are accepted' });
      return;
    }

    setUploadStatus({ type: 'loading', message: 'Uploading and parsing resume...' });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/resume/upload', formData);

      const newResume = {
        id: response.data.resume_id,
        fileUrl: response.data.file_url,
        fileName: file.name,
        uploadedAt: new Date().toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        }),
        hasAnalysis: false,
        score: null,
      };

      setResumes((prev) => [newResume, ...prev]);
      setUploadStatus({ type: 'success', message: `"${file.name}" uploaded successfully!` });

      setTimeout(() => setUploadStatus(null), 4000);
    } catch (err) {
      setUploadStatus({
        type: 'error',
        message: err.response?.data?.detail || 'Upload failed. Please try again.',
      });
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  });

  return (
    <>
      <Navbar />
      <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop py-stack-lg">
        {/* page header */}
        <div className="mb-stack-lg">
          <h1 className="font-display text-headline-lg text-on-surface">Your Dashboard</h1>
          <p className="mt-2 text-body-md text-on-surface-variant">
            Upload your resume and get AI-powered feedback instantly.
          </p>
        </div>

        {/* ── Upload Zone ─────────────────────────────────────── */}
        <div
          {...getRootProps()}
          className={`tonal-card rounded-2xl p-10 text-center cursor-pointer transition-all
                      border-2 border-dashed
                      ${isDragActive ? 'border-electric-indigo bg-electric-indigo/5' : 'border-outline-variant hover:border-electric-indigo'}`}
        >
          <input {...getInputProps()} />
          <span className="material-symbols-outlined text-electric-indigo text-5xl">cloud_upload</span>
          <h3 className="mt-3 text-headline-md font-display text-on-surface">
            {isDragActive ? 'Drop your resume here' : 'Upload Resume'}
          </h3>
          <p className="mt-2 text-body-md text-on-surface-variant">
            Drag and drop your PDF resume here, or click to browse. PDF only.
          </p>
          <span className="inline-block mt-4 bg-primary text-on-primary px-6 py-2 rounded-lg text-label-md font-label-md">
            Select File
          </span>
          <p className="mt-4 text-label-sm text-warning-amber">
            📱 Mobile upload is in development — use desktop for best experience.
          </p>
        </div>

        {/* upload status */}
        {uploadStatus && (
          <div
            className={`mt-4 flex items-center gap-2 px-4 py-3 rounded-lg text-label-md border
              ${uploadStatus.type === 'error'
                ? 'bg-error-crimson/10 text-error-crimson border-error-crimson/20'
                : uploadStatus.type === 'success'
                ? 'bg-success-teal/10 text-success-teal border-success-teal/20'
                : 'bg-electric-indigo/10 text-electric-indigo border-electric-indigo/20'}`}
          >
            <span className="material-symbols-outlined text-[20px]">
              {uploadStatus.type === 'error' ? 'error'
                : uploadStatus.type === 'success' ? 'check_circle'
                : 'sync'}
            </span>
            {uploadStatus.message}
          </div>
        )}

        {/* ── Resume List ─────────────────────────────────────── */}
        <div className="mt-stack-lg">
          {loadingHistory ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <div className="w-10 h-10 border-4 border-electric-indigo/20 border-t-electric-indigo rounded-full animate-spin" />
              <p className="text-body-md text-on-surface-variant">Loading your resumes...</p>
            </div>
          ) : resumes.length > 0 ? (
            <>
              <div className="flex items-center justify-between mb-stack-md">
                <h2 className="font-display text-headline-md text-on-surface">Your Resumes</h2>
                <span className="text-label-md text-on-surface-variant">{resumes.length} Total</span>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-gutter">
                {resumes.map((resume) => (
                  <div key={resume.id} className="tonal-card rounded-2xl p-6">
                    {/* card header */}
                    <div className="flex items-start justify-between">
                      <span className="material-symbols-outlined text-electric-indigo text-3xl">description</span>
                      {resume.hasAnalysis && resume.score !== null && (
                        <div className="flex items-center gap-2">
                          <div className="text-right">
                            <span className="block text-headline-md font-display text-on-surface leading-none">{resume.score}</span>
                            <span className="text-label-sm text-on-surface-variant">Score</span>
                          </div>
                          <span className="text-label-sm bg-success-teal/10 text-success-teal px-2 py-0.5 rounded-full">Reviewed</span>
                        </div>
                      )}
                    </div>

                    <h3 className="mt-4 text-label-md font-semibold text-on-surface">{resume.fileName}</h3>
                    <p className="text-label-sm text-on-surface-variant">
                      Uploaded {resume.uploadedAt} · ID: {resume.id}
                    </p>

                    {/* expandable analysis preview */}
                    {resume.hasAnalysis && (
                      <div className="mt-4">
                        <button
                          onClick={() => toggleExpand(resume.id)}
                          className="flex items-center gap-2 text-label-md text-on-surface-variant
                                     hover:text-primary transition-colors w-full text-left"
                        >
                          <span className="material-symbols-outlined text-[20px]">
                            {expandedCards[resume.id] ? 'expand_less' : 'expand_more'}
                          </span>
                          <span>
                            {resume.strengths?.length || 0} strengths ·{' '}
                            {resume.weaknesses?.length || 0} weaknesses ·{' '}
                            {resume.suggestions?.length || 0} suggestions
                          </span>
                        </button>

                        {expandedCards[resume.id] && (
                          <div className="mt-3 space-y-4">
                            {resume.strengths?.length > 0 && (
                              <div>
                                <p className="text-label-md font-semibold text-success-teal mb-1">Strengths</p>
                                <ul className="space-y-1">
                                  {resume.strengths.map((s, i) => (
                                    <li key={i} className="flex items-start gap-2 text-body-md text-on-surface-variant">
                                      <span className="material-symbols-outlined text-[18px] text-success-teal">check</span>
                                      {s}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {resume.weaknesses?.length > 0 && (
                              <div>
                                <p className="text-label-md font-semibold text-error-crimson mb-1">Weaknesses</p>
                                <ul className="space-y-1">
                                  {resume.weaknesses.map((w, i) => (
                                    <li key={i} className="flex items-start gap-2 text-body-md text-on-surface-variant">
                                      <span className="material-symbols-outlined text-[18px] text-error-crimson">close</span>
                                      {w}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {resume.suggestions?.length > 0 && (
                              <div>
                                <p className="text-label-md font-semibold text-warning-amber mb-1">Suggestions</p>
                                <ul className="space-y-1">
                                  {resume.suggestions.map((s, i) => (
                                    <li key={i} className="flex items-start gap-2 text-body-md text-on-surface-variant">
                                      <span className="material-symbols-outlined text-[18px] text-warning-amber">lightbulb</span>
                                      {s}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* action buttons */}
                    <div className="mt-5 space-y-2">
                      <button
                        onClick={() => navigate(`/review/${resume.id}`)}
                        className="w-full bg-electric-indigo text-white py-2 rounded-lg
                                   text-label-md font-label-md flex items-center justify-center gap-2
                                   hover:brightness-110 transition-all active:scale-95"
                      >
                        <span className="material-symbols-outlined text-[20px]">analytics</span>
                        {resume.hasAnalysis ? 'Re-Review' : 'AI Review'}
                      </button>
                      <button
                        onClick={() => setViewingResume(resume)}
                        className="w-full border border-slate-gray/20 text-primary py-2 rounded-lg
                                   text-label-md font-label-md flex items-center justify-center gap-2
                                   hover:bg-surface-container-low transition-all active:scale-95"
                      >
                        <span className="material-symbols-outlined text-[20px]">visibility</span>
                        View Resume
                      </button>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => navigate(`/evaluate/${resume.id}`)}
                          className="border border-slate-gray/20 text-primary py-2 rounded-lg
                                     text-label-md font-label-md hover:bg-surface-container-low transition-all"
                        >
                          Evaluate
                        </button>
                        <button
                          onClick={() => navigate(`/chat/${resume.id}`)}
                          className="border border-slate-gray/20 text-primary py-2 rounded-lg
                                     text-label-md font-label-md hover:bg-surface-container-low transition-all"
                        >
                          Chat
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          onClick={() => navigate(`/ats/${resume.id}`)}
                          className="border border-slate-gray/20 text-primary py-2 rounded-lg
                                     text-label-md font-label-md hover:bg-surface-container-low transition-all"
                        >
                          ATS Check
                        </button>
                        <button
                          onClick={() => navigate(`/rewrite/${resume.id}`)}
                          className="border border-slate-gray/20 text-primary py-2 rounded-lg
                                     text-label-md font-label-md hover:bg-surface-container-low transition-all"
                        >
                          Rewrite
                        </button>
                        <button
                          onClick={() => navigate(`/jobs/${resume.id}`)}
                          className="border border-slate-gray/20 text-primary py-2 rounded-lg
                                     text-label-md font-label-md hover:bg-surface-container-low transition-all"
                        >
                          Jobs
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            /* empty state */
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 rounded-full bg-surface-container-high flex items-center justify-center">
                <span className="material-symbols-outlined text-on-surface-variant text-3xl">description</span>
              </div>
              <h3 className="mt-4 text-headline-md font-display text-on-surface">No resumes yet</h3>
              <p className="mt-2 text-body-md text-on-surface-variant">
                Upload a PDF resume above to get started with AI-powered analysis.
              </p>
            </div>
          )}
        </div>
      </div>

      {viewingResume && (
        <ResumeViewerModal
          resumeId={viewingResume.id}
          title={viewingResume.fileName}
          onClose={() => setViewingResume(null)}
        />
      )}
    </>
  );
}
