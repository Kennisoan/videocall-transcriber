import React, { useState } from 'react';
import { fetcher } from '../../api/client';
import useSWR from 'swr';
import api from '../../api/client';
import styles from './App.module.css';
import RecordingsList from '../RecordingsList';
import PasswordForm from '../PasswordForm';
import ErrorBoundary from '../ErrorBoundary';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('authToken')
  );
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Use public endpoint for recorder state on login page
  const { data: stateData } = useSWR('/recorder_state', fetcher, {
    refreshInterval: 2000,
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isRegister) {
        // Register new user
        await api.post('/register', {
          username,
          password,
          name: null, // Optional field
        });
        // After successful registration, switch to login mode
        setIsRegister(false);
        setError('Регистрация успешна! Теперь вы можете войти.');
        setIsLoading(false);
        return;
      } else {
        // Login with username/password
        const response = await api.post(
          '/token',
          new URLSearchParams({
            username,
            password,
          }),
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          }
        );

        localStorage.setItem('authToken', response.data.access_token);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error(error);
      setError(
        error.response?.data?.detail || 'Ошибка аутентификации'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleLegacyLogin = async () => {
    try {
      // Try legacy login as fallback
      const response = await api.post('/login', { password });
      localStorage.setItem('authToken', response.data.token);
      setIsAuthenticated(true);
    } catch (error) {
      console.error(error);
      setError(error.response?.data?.detail || 'Login failed');
    }
  };

  if (!isAuthenticated) {
    return (
      <PasswordForm
        username={username}
        setUsername={setUsername}
        password={password}
        setPassword={setPassword}
        error={error}
        handleLogin={handleLogin}
        isRegister={isRegister}
        setIsRegister={setIsRegister}
        isLoading={isLoading}
      />
    );
  }

  return (
    <ErrorBoundary>
      <RecordingsList state={stateData?.state} />
    </ErrorBoundary>
  );
}

export default App;
