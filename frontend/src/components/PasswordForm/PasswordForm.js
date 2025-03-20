import React from 'react';
import { Lock, User, Loader } from 'react-feather';

import styles from './PasswordForm.module.css';

function PasswordForm({
  username,
  setUsername,
  password,
  setPassword,
  error,
  handleLogin,
  isRegister,
  setIsRegister,
  isLoading,
}) {
  return (
    <div className={styles.container}>
      <Lock size={48} className={styles.lockIcon} />
      <form className={styles.form} onSubmit={handleLogin}>
        <div className={styles.inputGroup}>
          <User size={20} className={styles.inputIcon} />
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Юзернейм"
            required
            disabled={isLoading}
          />
        </div>
        <div className={styles.inputGroup}>
          <Lock size={20} className={styles.inputIcon} />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Пароль"
            required
            disabled={isLoading}
          />
        </div>
        <button
          type="submit"
          className={styles.button}
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader size={16} className={styles.buttonLoader} />
          ) : isRegister ? (
            'Зарегистрироваться'
          ) : (
            'Войти'
          )}
        </button>
      </form>
      {error && <p className={styles.error}>{error}</p>}
      <p className={styles.switchMode}>
        {isRegister ? 'Уже есть аккаунт?' : 'Нужен аккаунт?'}
        <button
          className={styles.switchButton}
          onClick={() => setIsRegister(!isRegister)}
          disabled={isLoading}
        >
          {isRegister ? 'Войти' : 'Зарегистрироваться'}
        </button>
      </p>
    </div>
  );
}

export default PasswordForm;
