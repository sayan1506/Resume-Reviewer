import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  FiUploadCloud,
  FiFileText,
  FiSearch,
  FiClipboard,
  FiCheckCircle,
  FiStar,
  FiChevronDown,
  FiChevronUp,
  FiAlertCircle,
  FiZap,
} from 'react-icons/fi';
import api from '../api/axios';
import Navbar from '../components/Navbar';

export default function Dashboard() {
  const [resumes, setResumes] = useState([]);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [expandedCards, setExpandedCards] = useState({});
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
      <div className="dashboard-container">
        <div className="dashboard-header">
          <h1>Dashboard</h1>
          <p>Upload your resume and get AI-powered feedback instantly</p>
        </div>

        {/* Upload Zone */}
        <div className="upload-section">
          <div
            {...getRootProps()}
            className={`upload-zone ${isDragActive ? 'active' : ''}`}
          >
            <input {...getInputProps()} />
            <FiUploadCloud className="upload-icon" />
            <h3>{isDragActive ? 'Drop your resume here' : 'Upload Your Resume'}</h3>
            <p>Drag & drop a PDF file here, or click to browse</p>
          </div>

          {uploadStatus && (
            <div className={`upload-status ${uploadStatus.type}`}>
              {uploadStatus.message}
            </div>
          )}
        </div>

        {/* Resume List */}
        <div className="resumes-section">
          {loadingHistory ? (
            <div className="loading-container">
              <div className="spinner"></div>
              <p className="loading-text">Loading your resumes...</p>
            </div>
          ) : resumes.length > 0 ? (
            <>
              <h2>Your Resumes</h2>
              <div className="resume-grid">
                {resumes.map((resume) => (
                  <div key={resume.id} className="resume-card">
                    <div className="resume-card-header">
                      <div className="resume-card-icon">
                        <FiFileText />
                      </div>
                      <div className="resume-card-info">
                        <h3>{resume.fileName}</h3>
                        <p>Uploaded {resume.uploadedAt} • ID: {resume.id}</p>
                      </div>
                    </div>

                    {/* Show analysis score if available */}
                    {resume.hasAnalysis && (
                      <div className="resume-analysis-preview">
                        <div className="analysis-top-row" onClick={() => toggleExpand(resume.id)} style={{ cursor: 'pointer' }}>
                          <div className="analysis-score-badge">
                            <FiStar style={{ color: 'var(--warning)' }} />
                            <span className="analysis-score-value">{resume.score}</span>
                            <span className="analysis-score-label">/100</span>
                          </div>
                          <div className="analysis-summary">
                            <div className="analysis-stat">
                              <FiCheckCircle style={{ color: 'var(--success)', fontSize: '0.8rem' }} />
                              <span>{resume.strengths?.length || 0} strengths</span>
                            </div>
                            <div className="analysis-stat">
                              <span style={{ color: 'var(--text-muted)' }}>•</span>
                              <span>{resume.weaknesses?.length || 0} weaknesses</span>
                            </div>
                            <div className="analysis-stat">
                              <span style={{ color: 'var(--text-muted)' }}>•</span>
                              <span>{resume.suggestions?.length || 0} suggestions</span>
                            </div>
                          </div>
                          <button className="btn-expand" type="button">
                            {expandedCards[resume.id] ? <FiChevronUp /> : <FiChevronDown />}
                            <span>{expandedCards[resume.id] ? 'Hide' : 'View Details'}</span>
                          </button>
                        </div>

                        {/* Expanded details */}
                        {expandedCards[resume.id] && (
                          <div className="analysis-expanded">
                            {resume.strengths?.length > 0 && (
                              <div className="analysis-detail-section">
                                <h4><FiCheckCircle style={{ color: 'var(--success)' }} /> Strengths</h4>
                                <ul className="result-list strengths-list">
                                  {resume.strengths.map((s, i) => <li key={i}>{s}</li>)}
                                </ul>
                              </div>
                            )}
                            {resume.weaknesses?.length > 0 && (
                              <div className="analysis-detail-section">
                                <h4><FiAlertCircle style={{ color: 'var(--error)' }} /> Weaknesses</h4>
                                <ul className="result-list weaknesses-list">
                                  {resume.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
                                </ul>
                              </div>
                            )}
                            {resume.suggestions?.length > 0 && (
                              <div className="analysis-detail-section">
                                <h4><FiZap style={{ color: 'var(--info)' }} /> Suggestions</h4>
                                <ul className="result-list suggestions-list">
                                  {resume.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    <div className="resume-card-actions">
                      <button
                        className="btn-action btn-review"
                        onClick={() => navigate(`/review/${resume.id}`)}
                      >
                        <FiSearch />
                        {resume.hasAnalysis ? 'Re-Review' : 'AI Review'}
                      </button>
                      <button
                        className="btn-action btn-evaluate"
                        onClick={() => navigate(`/evaluate/${resume.id}`)}
                      >
                        <FiClipboard />
                        Evaluate
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📄</div>
              <h3>No resumes uploaded yet</h3>
              <p>Upload a PDF resume to get started with AI-powered analysis</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
