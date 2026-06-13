import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-slate-gray/10">
      <div className="max-w-max-width-content mx-auto px-margin-mobile sm:px-margin-desktop h-16 flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
            psychology
          </span>
          <span className="font-display font-bold text-on-surface text-lg">
            Resume Reviewer
          </span>
        </Link>

        {isAuthenticated && (
          <div className="flex items-center gap-6">
            <Link
              to="/dashboard"
              className="text-slate-gray text-label-md font-semibold hover:text-primary transition-colors"
            >
              Dashboard
            </Link>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-slate-gray text-label-md font-semibold
                         hover:text-error-crimson transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">logout</span>
              <span>Logout</span>
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
