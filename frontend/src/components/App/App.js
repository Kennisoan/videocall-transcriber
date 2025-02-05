import React, { useState } from 'react';
import axios from 'axios';
import useSWR from 'swr';
import RecordingsList from '../RecordingsList';
import PasswordForm from '../PasswordForm';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Add interceptor to add token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers['x-token'] = token;
  }
  return config;
});

// Fetcher function for SWR
const fetcher = (url) => api.get(url).then((res) => res.data);

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('authToken')
  );
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  // Fetch recorder state
  const { data: stateData } = useSWR('/recorder_state', fetcher, {
    refreshInterval: 2000,
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/login', { password });
      const { token } = response.data;
      localStorage.setItem('authToken', token);
      setIsAuthenticated(true);
      setError('');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  if (!isAuthenticated) {
    return (
      <PasswordForm
        password={password}
        setPassword={setPassword}
        error={error}
        handleLogin={handleLogin}
      />
    );
  }

  return <RecordingsList state={stateData?.state} />;
}

export default App;
