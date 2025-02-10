import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Enable cookie support
});

// Add interceptor to add token to all requests (for backward compatibility during migration)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers['x-token'] = token;
  }
  return config;
});

// Fetcher function for SWR
export const fetcher = (url) => api.get(url).then((res) => res.data);

export default api;
