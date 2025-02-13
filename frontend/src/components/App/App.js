import React, { useState } from 'react';
import { fetcher } from '../../api/client';
import useSWR from 'swr';
import api from '../../api/client';
import styles from './App.module.css';
import RecordingsList from '../RecordingsList';
import PasswordForm from '../PasswordForm';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('authToken')
  );
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const { data: stateData } = useSWR('/recorder_state', fetcher, {
    refreshInterval: 2000,
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/login', { password });
      localStorage.setItem('authToken', response.data.token);
      setIsAuthenticated(true);
      setError('');
    } catch (error) {
      console.error(error);
      setError(error.response?.data?.detail || 'Login failed');
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
