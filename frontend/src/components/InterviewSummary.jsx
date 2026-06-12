export default function InterviewSummary({ summary }) {
  const { total_score, max_score, percentage, overall_feedback,
          top_strength, top_improvement, turns } = summary;

  const grade =
    percentage >= 80 ? { label: 'Excellent', color: '#22c55e' } :
    percentage >= 60 ? { label: 'Good',      color: '#f59e0b' } :
                       { label: 'Needs Work', color: '#ef4444' };

  return (
    <div className="interview-summary">
      <h2>Interview Complete 🎉</h2>

      <div className="summary-score-row">
        <div className="summary-big-score" style={{ color: grade.color }}>
          {total_score}/{max_score}
        </div>
        <div>
          <div className="summary-grade" style={{ color: grade.color }}>{grade.label}</div>
          <div className="summary-pct">{percentage}%</div>
        </div>
      </div>

      <p className="summary-feedback">{overall_feedback}</p>

      <div className="summary-highlights">
        <div className="highlight-card highlight-positive">
          <span>🏆 Top Strength</span>
          <p>{top_strength}</p>
        </div>
        <div className="highlight-card highlight-improve">
          <span>🎯 Focus Area</span>
          <p>{top_improvement}</p>
        </div>
      </div>

      <details className="summary-turns">
        <summary>View all {turns.length} questions & answers</summary>
        {turns.map((t, i) => (
          <div key={i} className="summary-turn">
            <div className="summary-turn-q"><strong>Q{i + 1}:</strong> {t.question}</div>
            <div className="summary-turn-score">Score: {t.score}/10</div>
            <div className="summary-turn-a"><em>Your answer:</em> {t.answer}</div>
          </div>
        ))}
      </details>

      <button
        className="btn-restart-interview"
        onClick={() => window.location.reload()}
      >
        Start a New Interview
      </button>
    </div>
  );
}
