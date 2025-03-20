import React, { useState, useEffect } from 'react';
import Modal from '../Modal';
import TextInput from '../TextInput';
import api from '../../api/client';
import useSWR, { mutate } from 'swr';
import { fetcher } from '../../api/client';
import {
  Hash,
  Edit2,
  Save,
  LogOut,
  User,
  Loader,
} from 'react-feather';
import styles from './UserProfileModal.module.css';

function UserProfileModal({ root }) {
  const { data: userData, error: userError } = useSWR(
    '/users/me',
    fetcher
  );
  const { data: permissions, error: permissionsError } = useSWR(
    '/permissions/my',
    fetcher
  );

  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (userData) {
      setName(userData.name || '');
    }
  }, [userData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsSubmitting(true);

    try {
      await api.patch('/users/me/name', { name });
      setSuccess('Имя успешно обновлено');
      setIsEditing(false);

      // Refresh user data
      mutate('/users/me');
    } catch (err) {
      setError(
        'Ошибка при обновлении имени: ' +
          (err.response?.data?.detail || err.message)
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    window.location.reload();
  };

  const isLoading = !userData || !permissions;
  const hasPermissions = permissions && permissions.length > 0;

  return (
    <Modal
      title="Профиль пользователя"
      root={root}
      onClose={() => {
        setIsEditing(false);
        setError('');
        setSuccess('');
      }}
    >
      {isLoading ? (
        <div className={styles.loaderContainer}>
          <Loader size={24} className={styles.spinner} />
          <p>Загрузка данных пользователя...</p>
        </div>
      ) : (
        <>
          <div className={styles.profileSection}>
            <div className={styles.userInfo}>
              <div className={styles.userIcon}>
                <User size={24} />
              </div>
              <div className={styles.userDetails}>
                <div className={styles.usernameRow}>
                  <h3 className={styles.username}>
                    {userData.username}
                  </h3>
                </div>
                {isEditing ? (
                  <form
                    onSubmit={handleSubmit}
                    className={styles.nameForm}
                  >
                    <TextInput
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Введите ваше имя"
                      disabled={isSubmitting}
                      aria-label="Имя пользователя"
                    />
                    <button
                      type="submit"
                      className={styles.saveButton}
                      disabled={isSubmitting}
                      aria-label="Сохранить имя"
                    >
                      {isSubmitting ? (
                        <Loader
                          size={16}
                          className={styles.buttonSpinner}
                        />
                      ) : (
                        <Save size={16} />
                      )}
                    </button>
                  </form>
                ) : (
                  <div className={styles.nameRow}>
                    <p className={styles.userFullName}>
                      {userData.name || 'Имя не указано'}
                    </p>
                    <button
                      className={styles.editButton}
                      onClick={() => setIsEditing(true)}
                      aria-label="Редактировать имя"
                    >
                      <Edit2 size={14} />
                    </button>
                  </div>
                )}
                {error && (
                  <p className={styles.error} role="alert">
                    {error}
                  </p>
                )}
                {success && (
                  <p className={styles.success} role="status">
                    {success}
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Доступные каналы</h3>
            {!hasPermissions ? (
              <p className={styles.noPermissions}>
                У вас нет доступа ни к одной группе. Обратитесь к
                администратору для получения прав доступа.
              </p>
            ) : (
              <div className={styles.permissionsList} role="list">
                {permissions.map((permission) => (
                  <div
                    key={permission.id}
                    className={styles.permissionItem}
                    role="listitem"
                  >
                    <Hash
                      size={16}
                      className={styles.hashIcon}
                      aria-hidden="true"
                    />
                    <span className={styles.groupName}>
                      {permission.group_name}
                    </span>
                    {permission.can_edit && (
                      <span className={styles.editBadge}>
                        Редактирование
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className={styles.actionSection}>
            <button
              className={styles.logoutButton}
              onClick={handleLogout}
            >
              <LogOut size={16} />
              Выйти из системы
            </button>
          </div>
        </>
      )}
    </Modal>
  );
}

export default UserProfileModal;
