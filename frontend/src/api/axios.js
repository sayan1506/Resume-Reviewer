import axios from 'axios';

const api = axios.create({
  baseURL: 'https://resume-reviewer-yqdp.onrender.com',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
