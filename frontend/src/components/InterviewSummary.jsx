export default function InterviewSummary({ summary }) {
  const { total_score, max_score, percentage, overall_feedback,
          top_strength, top_improvement, turns } = summary;

  const grade = percentage >= 80 ? { label: 'Excellent', color: 'text-success-teal', bg: 'bg-success-teal/10' }
              : percentage >= 60 ? { label: 'Good',      color: 'text-warning-amber', bg: 'bg-warning-amber/10' }
              :                    { label: 'Needs Work', color: 'text-error-crimson',  bg: 'bg-error-crimson/10' };

  return (
    <div className="tonal-card rounded-2xl p-6 my-2">
      {/* header + score */}
      <h2 className="text-headline-md font-display text-on-surface">Interview Complete 🎉</h2>

      <div className="mt-4 flex items-center gap-4">
        <div className={`text-headline-lg font-display ${grade.color}`}>
          {total_score}/{max_score}
        </div>
        <div>
          <div className={`inline-block px-3 py-1 rounded-full text-label-md font-semibold ${grade.color} ${grade.bg}`}>
            {grade.label}
          </div>
          <div className="text-body-md text-on-surface-variant mt-1">{percentage}%</div>
        </div>
      </div>

      <p className="mt-4 text-body-md text-on-surface-variant">{overall_feedback}</p>

      {/* highlights */}
      <div className="mt-4 grid sm:grid-cols-2 gap-3">
        <div className="rounded-xl bg-success-teal/10 p-4">
          <p className="text-label-md font-semibold text-on-surface">🏆 Top Strength</p>
          <p className="mt-1 text-body-md text-on-surface-variant">{top_strength}</p>
        </div>
        <div className="rounded-xl bg-warning-amber/10 p-4">
          <p className="text-label-md font-semibold text-on-surface">🎯 Focus Area</p>
          <p className="mt-1 text-body-md text-on-surface-variant">{top_improvement}</p>
        </div>
      </div>

      {/* Q&A history */}
      <details className="mt-4 group">
        <summary className="flex items-center gap-2 cursor-pointer text-label-md font-semibold text-primary">
          <span className="material-symbols-outlined text-[20px] group-open:rotate-90 transition-transform">chevron_right</span>
          View all {turns.length} questions &amp; answers
        </summary>
        <div className="mt-3 space-y-3">
          {turns.map((t, i) => (
            <div key={i} className="rounded-xl border border-outline-variant p-4">
              <div className="text-body-md font-semibold text-on-surface">Q{i + 1}: {t.question}</div>
              <div className="mt-1 text-label-sm text-on-surface-variant">Score: {t.score}/10</div>
              <div className="mt-1 text-body-md text-on-surface-variant">{t.answer}</div>
            </div>
          ))}
        </div>
      </details>

      {/* restart */}
      <button
        onClick={() => window.location.reload()}
        className="mt-6 w-full bg-electric-indigo text-white py-3.5 rounded-xl text-label-md
                   font-label-md font-bold hover:shadow-lg hover:shadow-electric-indigo/20
                   active:scale-95 transition-all flex items-center justify-center gap-2"
      >
        <span className="material-symbols-outlined text-[20px]">refresh</span>
        Start a New Interview
      </button>
    </div>
  );
}
