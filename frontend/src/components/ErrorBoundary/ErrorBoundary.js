import React from 'react';
import { AlertTriangle } from 'react-feather';
import styles from './ErrorBoundary.module.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // You can log the error to an error reporting service
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    this.setState({
      errorInfo: errorInfo,
    });
  }

  render() {
    if (this.state.hasError) {
      // Check if error is related to permissions
      const isPermissionError =
        (this.state.error &&
          this.state.error.message &&
          this.state.error.message
            .toLowerCase()
            .includes('permission')) ||
        (this.state.error &&
          this.state.error.message &&
          this.state.error.message
            .toLowerCase()
            .includes('access denied')) ||
        (this.state.error &&
          this.state.error.response &&
          this.state.error.response.status === 403);

      return (
        <div className={styles.errorContainer}>
          <AlertTriangle size={48} className={styles.errorIcon} />
          <h2 className={styles.errorTitle}>
            {isPermissionError
              ? 'Доступ запрещен'
              : 'Произошла ошибка'}
          </h2>
          <p className={styles.errorMessage}>
            {isPermissionError
              ? 'У вас нет прав для доступа к этой записи. Обратитесь к администратору.'
              : 'Что-то пошло не так. Попробуйте обновить страницу или обратитесь к администратору.'}
          </p>
          <button
            className={styles.reloadButton}
            onClick={() => window.location.reload()}
          >
            Обновить страницу
          </button>
          <p className={styles.errorDetails}>
            {this.state.error && this.state.error.toString()}
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
