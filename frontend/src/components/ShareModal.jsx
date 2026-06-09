import { useState } from 'react';
import { FiCopy, FiCheck, FiX } from 'react-icons/fi';

export default function ShareModal({ shareUrl, onClose }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Share Report</h3>
          <button className="modal-close" onClick={onClose}><FiX /></button>
        </div>
        <p className="modal-subtitle">Anyone with this link can view this report (no login required).</p>
        <div className="share-url-row">
          <input className="share-url-input" value={shareUrl} readOnly />
          <button className="btn-copy" onClick={handleCopy}>
            {copied ? <FiCheck /> : <FiCopy />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>
    </div>
  );
}
