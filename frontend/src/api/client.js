import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Enable cookie support
});

// Add interceptor to add token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    // Add token to header for new auth system
    config.headers['Authorization'] = `Bearer ${token}`;

    // Keep x-token for backward compatibility
    config.headers['x-token'] = token;
  }
  return config;
});

// Handle 401 responses by redirecting to login if not a login request
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Don't auto-redirect on authentication endpoints
    const isAuthRequest =
      error.config.url === '/token' ||
      error.config.url === '/login' ||
      error.config.url === '/register';

    if (
      error.response &&
      error.response.status === 401 &&
      !isAuthRequest
    ) {
      // Clear token and reload to show login form
      localStorage.removeItem('authToken');
      window.location.reload();
    }

    return Promise.reject(error);
  }
);

// Fetcher function for SWR
export const fetcher = (url) => api.get(url).then((res) => res.data);

export default api;
