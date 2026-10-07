import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Attach JWT token for every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Let the AI read dates and regional resume norms in the user's context
    // (e.g. 05/06/2025 is 5 June in India but May 6 in the US).
    try {
      config.headers['X-User-Locale'] = navigator.language;
      config.headers['X-User-Timezone'] = Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
      // Headers are optional; the backend falls back to neutral defaults.
    }
    if (!(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Show session-expired message then redirect on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.setItem(
        'session_expired',
        'Your session has expired. Please sign in again.'
      );
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
