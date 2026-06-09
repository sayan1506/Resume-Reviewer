import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import ReviewResults from './pages/ReviewResults';
import Evaluate from './pages/Evaluate';
import ChatPage from './pages/ChatPage';
import SharedReportPage from './pages/SharedReportPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
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
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
