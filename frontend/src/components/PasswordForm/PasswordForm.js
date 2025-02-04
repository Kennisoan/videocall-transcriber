import React from 'react';
import { Lock } from 'react-feather';

import styles from './PasswordForm.module.css';

function PasswordForm({ password, setPassword, error, handleLogin }) {
  return (
    <div className={styles.container}>
      <Lock size={48} className={styles.lockIcon} />
      <form className={styles.form} onSubmit={handleLogin}>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Введите пароль"
        />
        <button type="submit" className={styles.button}>
          Войти
        </button>
      </form>
      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}

export default PasswordForm;
