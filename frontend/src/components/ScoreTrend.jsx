import { useMemo } from 'react';

/**
 * Score-over-time line chart for a resume's review history.
 * Hand-rolled SVG (no chart dependency). Renders nothing with fewer than 2 points.
 *
 * @param {{ history: Array<{score:number, created_at:string}> }} props
 */
export default function ScoreTrend({ history }) {
  const points = useMemo(() => {
    if (!history || history.length < 2) return null;

    const width = 600;
    const height = 220;
    const pad = { top: 24, right: 24, bottom: 36, left: 40 };
    const innerW = width - pad.left - pad.right;
    const innerH = height - pad.top - pad.bottom;
    const n = history.length;

    const xFor = (i) => pad.left + (i / (n - 1)) * innerW;
    const yFor = (score) => pad.top + (1 - Math.max(0, Math.min(100, score)) / 100) * innerH;

    const pts = history.map((h, i) => ({
      x: xFor(i),
      y: yFor(h.score),
      score: h.score,
      created_at: h.created_at,
    }));

    const linePath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');

    return { width, height, pad, innerW, innerH, pts, linePath };
  }, [history]);

  if (!points) return null;

  const { width, height, pad, innerW, pts, linePath } = points;
  const first = history[0].score;
  const last = history[history.length - 1].score;
  const delta = last - first;
  const deltaColor =
    delta > 0 ? 'text-success-teal' : delta < 0 ? 'text-error-crimson' : 'text-on-surface-variant';
  const deltaSign = delta > 0 ? '+' : '';

  const fmtDate = (iso) => {
    if (!iso) return '';
    // Backend sends Python str(datetime) like "2026-06-19 14:21:12+00:00";
    // normalize the space separator to 'T' so all browsers parse it.
    const d = new Date(iso.replace(' ', 'T'));
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  return (
    <div className="tonal-card rounded-2xl p-6">
      <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-electric-indigo">trending_up</span>
          <h2 className="text-headline-md font-display text-on-surface">Score Trend</h2>
        </div>
        <div className={`text-label-md font-label-md ${deltaColor}`}>
          {deltaSign}{delta} since first review · {history.length} reviews
        </div>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto"
        role="img"
        aria-label={`Resume score trend across ${history.length} reviews, latest score ${last} out of 100`}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* horizontal gridlines at 0 / 50 / 100 */}
        {[0, 50, 100].map((g) => {
          const y = pad.top + (1 - g / 100) * (height - pad.top - pad.bottom);
          return (
            <g key={g}>
              <line
                x1={pad.left}
                y1={y}
                x2={pad.left + innerW}
                y2={y}
                stroke="#e2e7ff"
                strokeWidth="1"
              />
              <text x={pad.left - 8} y={y + 4} textAnchor="end" className="fill-on-surface-variant" fontSize="11">
                {g}
              </text>
            </g>
          );
        })}

        {/* connecting line */}
        <path d={linePath} fill="none" stroke="currentColor" strokeWidth="2.5" className="text-electric-indigo" />

        {/* points + date labels */}
        {pts.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="4.5" className="fill-electric-indigo" />
            <text x={p.x} y={p.y - 10} textAnchor="middle" className="fill-on-surface" fontSize="11" fontWeight="600">
              {p.score}
            </text>
            <text
              x={p.x}
              y={height - pad.bottom + 18}
              textAnchor="middle"
              className="fill-on-surface-variant"
              fontSize="10"
            >
              {fmtDate(p.created_at)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
