import { useState, useEffect } from 'react';
import api from '../api/axios';

export default function ResumeViewerModal({ resumeId, title, onClose }) {
  const [url, setUrl] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchUrl = async () => {
      try {
        const response = await api.get(`/resume/${resumeId}/view`);
        if (!cancelled) setUrl(response.data.url);
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.data?.detail || 'Could not load the resume. Please try again.'
          );
        }
      }
    };

    fetchUrl();
    return () => {
      cancelled = true;
    };
  }, [resumeId]);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-on-surface/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="tonal-card rounded-2xl w-full max-w-4xl h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-outline-variant">
          <h3 className="text-headline-md font-display text-on-surface truncate">
            {title || 'Resume'}
          </h3>
          <div className="flex items-center gap-2">
            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 bg-electric-indigo text-white px-4 py-2 rounded-lg
                           text-label-md font-label-md hover:brightness-110 active:scale-95 transition-all"
              >
                <span className="material-symbols-outlined text-[20px]">download</span>
                Download
              </a>
            )}
            <button
              onClick={onClose}
              className="w-9 h-9 flex items-center justify-center rounded-lg text-on-surface-variant
                         hover:bg-surface-container-low transition-all"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        {/* body */}
        <div className="flex-1 bg-surface-container-low">
          {error ? (
            <div className="h-full flex flex-col items-center justify-center gap-3 text-center px-6">
              <span className="material-symbols-outlined text-error-crimson text-4xl">error</span>
              <p className="text-body-md text-on-surface-variant">{error}</p>
            </div>
          ) : url ? (
            <iframe
              src={url}
              title={title || 'Resume'}
              className="w-full h-full border-0"
            />
          ) : (
            <div className="h-full flex flex-col items-center justify-center gap-4">
              <div className="w-10 h-10 border-4 border-electric-indigo/20 border-t-electric-indigo rounded-full animate-spin" />
              <p className="text-body-md text-on-surface-variant">Loading your resume...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
