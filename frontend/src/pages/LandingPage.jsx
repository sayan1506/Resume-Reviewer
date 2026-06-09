import { useNavigate } from 'react-router-dom';
import { FiFileText, FiCpu, FiTarget, FiArrowRight } from 'react-icons/fi';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing-page">
      {/* Navbar */}
      <nav className="landing-navbar">
        <div className="landing-navbar-content">
          <div className="landing-brand">
            <FiFileText className="landing-brand-icon" />
            <span>Resume Reviewer</span>
          </div>
          <div className="landing-nav-actions">
            <button className="btn-nav-login" onClick={() => navigate('/login')}>
              Login
            </button>
            <button className="btn-nav-signup" onClick={() => navigate('/signup')}>
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-hero-content">
          <h1 className="landing-hero-title">
            Know exactly how strong your resume is before you apply
          </h1>
          <p className="landing-hero-subtitle">
            AI-powered resume scoring, interview prep, and skill gap analysis — in seconds.
          </p>
          <button className="btn-hero-cta" onClick={() => navigate('/signup')}>
            Get Started <FiArrowRight />
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="landing-features">
        <div className="landing-features-content">
          <div className="feature-card">
            <div className="feature-icon">
              <FiFileText />
            </div>
            <h3 className="feature-title">Upload Your Resume</h3>
            <p className="feature-description">
              Upload your PDF resume securely. Parsed and analysed instantly.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <FiCpu />
            </div>
            <h3 className="feature-title">AI-Powered Review</h3>
            <p className="feature-description">
              Get a detailed score with strengths, weaknesses, and improvement suggestions.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <FiTarget />
            </div>
            <h3 className="feature-title">Interview Prep Report</h3>
            <p className="feature-description">
              Receive tailored technical and behavioural questions, skill gap analysis, and a day-by-day prep plan.
            </p>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="landing-testimonials">
        <div className="landing-testimonials-content">
          <div className="testimonial-card">
            <p className="testimonial-quote">
              "This tool helped me land interviews at 3 companies in 2 weeks."
            </p>
            <p className="testimonial-author">— Priya S., Software Engineer</p>
          </div>

          <div className="testimonial-card">
            <p className="testimonial-quote">
              "The interview prep plan was shockingly accurate. Knew exactly what to study."
            </p>
            <p className="testimonial-author">— Arjun M., Data Analyst</p>
          </div>

          <div className="testimonial-card">
            <p className="testimonial-quote">
              "Finally an AI tool that gives real, actionable feedback instead of vague suggestions."
            </p>
            <p className="testimonial-author">— Sneha R., Product Manager</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-content">
          <div className="footer-brand">
            <h4>Resume Reviewer</h4>
            <p>AI-powered resume analysis and interview prep</p>
          </div>
          <div className="footer-links">
            <button onClick={() => navigate('/login')}>Login</button>
            <span>·</span>
            <button onClick={() => navigate('/signup')}>Sign Up</button>
          </div>
          <div className="footer-copyright">
            <p>© {new Date().getFullYear()} Resume Reviewer. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
