import { useState } from 'react';

export default function ShareModal({ shareUrl, onClose }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-on-surface/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="tonal-card rounded-2xl w-full max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* header */}
        <div className="flex items-center justify-between">
          <h3 className="text-headline-md font-display text-on-surface">Share Analysis</h3>
          <button
            onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-lg text-on-surface-variant
                       hover:bg-surface-container-low transition-all"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* body */}
        <p className="mt-2 text-body-md text-on-surface-variant">
          Anyone with this link can view this report (no login required).
        </p>
        <div className="mt-4 flex items-center gap-2">
          <input
            value={shareUrl}
            readOnly
            className="flex-1 px-4 py-3 rounded-lg border border-outline-variant bg-white
                       text-body-md text-on-surface-variant outline-none"
          />
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 bg-electric-indigo text-white px-4 py-3 rounded-lg
                       text-label-md font-label-md hover:brightness-110 active:scale-95 transition-all"
          >
            <span className="material-symbols-outlined text-[20px]">
              {copied ? 'check' : 'content_copy'}
            </span>
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>
    </div>
  );
}
