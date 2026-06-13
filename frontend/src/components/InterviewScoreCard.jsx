export default function InterviewScoreCard({ feedback }) {
  const { score, strengths, improvements, ideal_answer_hint } = feedback;
  const colorClass = score >= 8 ? 'border-success-teal text-success-teal'
                   : score >= 5 ? 'border-warning-amber text-warning-amber'
                   : 'border-error-crimson text-error-crimson';

  return (
    <div className="tonal-card rounded-2xl p-6 my-2">
      {/* score circle + title */}
      <div className="flex items-center gap-4">
        <div className={`w-16 h-16 rounded-full border-4 flex items-baseline justify-center ${colorClass}`}>
          <span className="text-headline-md font-display">{score}</span>
          <span className="text-label-sm">/10</span>
        </div>
        <h3 className="text-headline-md font-display text-on-surface">Answer Feedback</h3>
      </div>

      {/* what you did well */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="material-symbols-outlined text-[20px] text-success-teal">check_circle</span>
          <h4 className="text-label-md font-semibold text-on-surface">What you did well</h4>
        </div>
        <ul className="space-y-1">
          {strengths.map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-body-md text-on-surface-variant">
              <span className="material-symbols-outlined text-[18px] text-success-teal">check</span>
              {s}
            </li>
          ))}
        </ul>
      </div>

      {/* areas to improve */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="material-symbols-outlined text-[20px] text-warning-amber">warning</span>
          <h4 className="text-label-md font-semibold text-on-surface">Areas to improve</h4>
        </div>
        <ul className="space-y-1">
          {improvements.map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-body-md text-on-surface-variant">
              <span className="material-symbols-outlined text-[18px] text-error-crimson">close</span>
              {s}
            </li>
          ))}
        </ul>
      </div>

      {/* hint */}
      <div className="mt-4 rounded-xl bg-surface-container-low p-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="material-symbols-outlined text-[20px] text-warning-amber">lightbulb</span>
          <h4 className="text-label-md font-semibold text-on-surface">Ideal Answer Hint</h4>
        </div>
        <p className="text-body-md text-on-surface-variant">{ideal_answer_hint}</p>
      </div>
    </div>
  );
}
