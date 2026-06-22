import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import ReviewResults from './pages/ReviewResults';
import Evaluate from './pages/Evaluate';
import ChatPage from './pages/ChatPage';
import CoverLetter from './pages/CoverLetter';
import ATSCheck from './pages/ATSCheck';
import Rewrite from './pages/Rewrite';
import JobMatch from './pages/JobMatch';
import SharedReportPage from './pages/SharedReportPage';

export default function App() {
  // Warm-up ping to prevent Render cold starts
  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/health`).catch(() => {});
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/shared/:token" element={<SharedReportPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review/:resumeId"
            element={
              <ProtectedRoute>
                <ReviewResults />
              </ProtectedRoute>
            }
          />
          <Route
            path="/evaluate/:resumeId"
            element={
              <ProtectedRoute>
                <Evaluate />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat/:resumeId"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/cover-letter/:resumeId"
            element={
              <ProtectedRoute>
                <CoverLetter />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ats/:resumeId"
            element={
              <ProtectedRoute>
                <ATSCheck />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rewrite/:resumeId"
            element={
              <ProtectedRoute>
                <Rewrite />
              </ProtectedRoute>
            }
          />
          <Route
            path="/jobs/:resumeId"
            element={
              <ProtectedRoute>
                <JobMatch />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
