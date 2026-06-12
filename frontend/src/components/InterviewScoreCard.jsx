import { FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

export default function InterviewScoreCard({ feedback }) {
  const { score, strengths, improvements, ideal_answer_hint } = feedback;
  const color = score >= 8 ? '#22c55e' : score >= 5 ? '#f59e0b' : '#ef4444';

  return (
    <div className="score-card">
      <div className="score-card-header">
        <div className="score-circle" style={{ borderColor: color, color }}>
          <span className="score-value">{score}</span>
          <span className="score-denom">/10</span>
        </div>
        <div className="score-card-title">Answer Feedback</div>
      </div>

      <div className="score-card-section">
        <h4><FiCheckCircle className="icon-green" /> What you did well</h4>
        <ul>{strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
      </div>

      <div className="score-card-section">
        <h4><FiAlertCircle className="icon-amber" /> Areas to improve</h4>
        <ul>{improvements.map((s, i) => <li key={i}>{s}</li>)}</ul>
      </div>

      <div className="score-card-hint">
        <strong>💡 Hint:</strong> {ideal_answer_hint}
      </div>
    </div>
  );
}
