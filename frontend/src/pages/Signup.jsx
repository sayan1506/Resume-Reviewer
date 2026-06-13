import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function GoogleSignupButton({ onSuccess, onError, disabled, loading }) {
  const handleGoogleSignup = useGoogleLogin({
    flow: 'auth-code',
    onSuccess,
    onError,
  });

  return (
    <button
      type="button"
      onClick={handleGoogleSignup}
      disabled={disabled}
      className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-lg
                 border border-outline-variant hover:bg-surface-container-low
                 transition-all duration-200 active:scale-[0.98] text-on-surface text-label-md font-semibold"
    >
      {loading ? (
        <span className="text-on-surface-variant">Signing up...</span>
      ) : (
        <>
          <svg viewBox="0 0 24 24" width="18" height="18" className="flex-shrink-0">
            <path
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              fill="#4285F4"
            />
            <path
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              fill="#FBBC05"
            />
            <path
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              fill="#EA4335"
            />
          </svg>
          Continue with Google
        </>
      )}
    </button>
  );
}

export default function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState('');
  const { signup, googleLogin, error, loading, googleLoading, setError } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setError('');

    if (password !== confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters');
      return;
    }

    const success = await signup(email, password);
    if (success) {
      navigate('/dashboard');
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center px-margin-mobile overflow-hidden bg-surface">
      {/* subtle background orbs */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-primary-fixed-dim/30 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 rounded-full bg-secondary-fixed-dim/30 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="tonal-card rounded-2xl p-8">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-3">
              <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                psychology
              </span>
            </div>
            <h1 className="font-display font-bold text-on-surface text-headline-md">Create Account</h1>
            <p className="text-on-surface-variant text-body-md mt-1">
              Get started with AI-powered resume reviews
            </p>
          </div>

          {(error || localError) && (
            <div className="flex items-center gap-2 mb-6 px-4 py-3 rounded-lg bg-error-crimson/10
                            border border-error-crimson/20 text-error-crimson text-label-md">
              <span className="material-symbols-outlined text-[20px]">error</span>
              <span>{localError || error}</span>
            </div>
          )}

          {/* Google OAuth */}
          {googleClientId && (
            <>
              <GoogleSignupButton
                onSuccess={async (response) => {
                  const success = await googleLogin(response.code);
                  if (success) navigate('/dashboard');
                }}
                onError={() => setError('Google sign-in was cancelled')}
                disabled={googleLoading}
                loading={googleLoading}
              />
              <div className="flex items-center gap-3 my-6">
                <div className="flex-1 h-px bg-outline-variant" />
                <span className="text-on-surface-variant text-label-sm uppercase tracking-wide">OR</span>
                <div className="flex-1 h-px bg-outline-variant" />
              </div>
            </>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block mb-1.5 text-label-md text-on-surface-variant">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-white border border-slate-gray/20 rounded-lg
                           focus:ring-2 focus:ring-primary/20 focus:border-primary
                           outline-none transition-all placeholder:text-slate-gray/40 text-body-md"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block mb-1.5 text-label-md text-on-surface-variant">
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="Min 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full px-4 py-3 bg-white border border-slate-gray/20 rounded-lg
                           focus:ring-2 focus:ring-primary/20 focus:border-primary
                           outline-none transition-all placeholder:text-slate-gray/40 text-body-md"
              />
            </div>

            {/* Confirm password */}
            <div>
              <label htmlFor="confirmPassword" className="block mb-1.5 text-label-md text-on-surface-variant">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-white border border-slate-gray/20 rounded-lg
                           focus:ring-2 focus:ring-primary/20 focus:border-primary
                           outline-none transition-all placeholder:text-slate-gray/40 text-body-md"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary text-on-primary py-3 rounded-lg text-label-md font-label-md
                         hover:bg-primary-container transition-all active:scale-95 disabled:opacity-60"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <div className="text-center mt-6 text-on-surface-variant text-body-md">
            Already have an account?{' '}
            <Link to="/login" className="text-primary font-semibold hover:underline">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
