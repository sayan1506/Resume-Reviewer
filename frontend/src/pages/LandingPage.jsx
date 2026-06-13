import { useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      {/* ── Navbar ─────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-slate-gray/10">
        <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
              psychology
            </span>
            <span className="font-display font-bold text-on-surface text-lg">
              Resume Reviewer
            </span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/login')}
              className="hidden sm:block text-slate-gray text-label-md font-semibold hover:text-primary transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => navigate('/signup')}
              className="bg-primary text-on-primary px-6 py-2 rounded-lg text-label-md
                         font-label-md hover:shadow-lg active:scale-95 transition-all"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop py-20 text-center">
          {/* pill badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-fixed text-primary mb-6">
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
            <span className="text-label-sm font-semibold">AI-Powered Career Intelligence</span>
          </div>

          <h1 className="font-display text-headline-lg-mobile sm:text-headline-xl text-on-surface max-w-3xl mx-auto">
            Know exactly how strong your resume is{' '}
            <span className="text-electric-indigo">before you apply</span>
          </h1>

          <p className="mt-6 text-body-lg text-on-surface-variant max-w-2xl mx-auto">
            AI-powered resume scoring, interview prep, and skill gap analysis — in seconds.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/signup')}
              className="bg-electric-indigo text-white px-8 py-4 rounded-xl text-label-md font-label-md
                         shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all flex items-center gap-2"
            >
              Get Started Free
              <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
            </button>
            <button
              onClick={() => navigate('/login')}
              className="bg-white border border-slate-gray/20 text-slate-gray px-8 py-4 rounded-xl
                         text-label-md font-label-md hover:bg-surface-container-low transition-all"
            >
              Sign In
            </button>
          </div>

          {/* hero score mockup */}
          <div className="mt-16 max-w-md mx-auto">
            <div className="tonal-card rounded-3xl p-8">
              <div className="flex flex-col items-center">
                <div className="relative w-40 h-40">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 192 192">
                    <circle cx="96" cy="96" r="88" fill="none" stroke="#e2e7ff" strokeWidth="12" />
                    <circle
                      cx="96" cy="96" r="88" fill="none" stroke="#14B8A6" strokeWidth="12"
                      strokeLinecap="round" strokeDasharray="552.92" strokeDashoffset={552.92 * (1 - 82 / 100)}
                      className="text-success-teal"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-headline-lg font-display text-on-surface">82</span>
                    <span className="text-label-sm text-on-surface-variant">OUT OF 100</span>
                  </div>
                </div>
                <p className="mt-4 text-headline-md font-display text-success-teal">Resume Score: Excellent</p>
                <p className="mt-1 text-body-md text-on-surface-variant">
                  You're in the top 5% of candidates for this role.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────── */}
      <section className="py-20">
        <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop">
          <div className="text-center mb-12">
            <h2 className="font-display text-headline-lg text-on-surface">Engineered for Your Advantage</h2>
            <p className="mt-3 text-body-lg text-on-surface-variant">
              Comprehensive AI tools built to decode recruitment logic.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-gutter">
            {/* card 1 */}
            <div className="tonal-card rounded-2xl p-8">
              <span className="material-symbols-outlined text-electric-indigo text-3xl">description</span>
              <h3 className="mt-4 text-headline-md font-display text-on-surface">Upload Your Resume</h3>
              <p className="mt-2 text-body-md text-on-surface-variant">
                Upload your PDF resume securely. Parsed and analysed instantly with industry-standard NLP.
              </p>
            </div>

            {/* card 2 */}
            <div className="tonal-card rounded-2xl p-8">
              <span className="material-symbols-outlined text-electric-indigo text-3xl">analytics</span>
              <h3 className="mt-4 text-headline-md font-display text-on-surface">AI-Powered Review</h3>
              <p className="mt-2 text-body-md text-on-surface-variant">
                Get a detailed score with strengths, weaknesses, and improvement suggestions.
              </p>
            </div>

            {/* card 3 */}
            <div className="tonal-card rounded-2xl p-8 md:col-span-2 lg:col-span-1">
              <span className="material-symbols-outlined text-electric-indigo text-3xl">psychology</span>
              <h3 className="mt-4 text-headline-md font-display text-on-surface">Interview Prep Report</h3>
              <p className="mt-2 text-body-md text-on-surface-variant">
                Receive tailored technical and behavioural questions, skill gap analysis, and a day-by-day prep plan.
              </p>
              <button
                onClick={() => navigate('/signup')}
                className="mt-6 whitespace-nowrap bg-on-surface text-white px-10 py-4 rounded-xl
                           text-label-md font-label-md hover:bg-slate-800 transition-all"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Testimonials ─────────────────────────────────────────── */}
      <section className="py-20 bg-surface-container-low">
        <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop">
          <div className="text-center mb-12">
            <h2 className="font-display text-headline-lg text-on-surface">What our users say</h2>
            <p className="mt-3 text-body-lg text-on-surface-variant">Real feedback from real candidates.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-gutter">
            {[
              { quote: 'This tool helped me land interviews at 3 companies in 2 weeks.', author: 'Priya S.', role: 'Software Engineer' },
              { quote: 'The interview prep plan was shockingly accurate. Knew exactly what to study.', author: 'Arjun M.', role: 'Data Analyst' },
              { quote: 'Finally an AI tool that gives real, actionable feedback instead of vague suggestions.', author: 'Sneha R.', role: 'Product Manager' },
            ].map((t, i) => (
              <div key={i} className="tonal-card rounded-2xl p-8">
                <span className="material-symbols-outlined text-electric-indigo text-3xl">format_quote</span>
                <p className="mt-2 text-body-md text-on-surface">"{t.quote}"</p>
                <div className="mt-4">
                  <p className="text-label-md font-semibold text-on-surface">{t.author}</p>
                  <p className="text-label-sm text-on-surface-variant">{t.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Band ─────────────────────────────────────────────── */}
      <section className="py-20 bg-primary">
        <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop text-center">
          <h2 className="font-display text-headline-lg text-on-primary">Ready to transform your career path?</h2>
          <p className="mt-3 text-body-lg text-on-primary/80">Get your free resume analysis today.</p>
          <button
            onClick={() => navigate('/signup')}
            className="mt-8 bg-white text-primary px-10 py-4 rounded-xl text-label-md
                       font-label-md hover:shadow-xl hover:bg-ice-white transition-all"
          >
            Start Your Review
          </button>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="py-12 border-t border-slate-gray/10">
        <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop
                        flex flex-col sm:flex-row items-center justify-between gap-6">
          <div>
            <h4 className="font-display font-bold text-on-surface">Resume Reviewer AI</h4>
            <p className="text-body-md text-on-surface-variant">AI-powered resume analysis and interview prep</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/login')}
              className="text-slate-gray text-label-sm hover:text-primary transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => navigate('/signup')}
              className="text-slate-gray text-label-sm hover:text-primary transition-colors"
            >
              Sign Up
            </button>
          </div>
          <p className="text-label-sm text-on-surface-variant">
            © {new Date().getFullYear()} Resume Reviewer. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
