import React, { useState, useEffect } from 'react';
import Modal from '../Modal';
import {
  Edit2,
  Save,
  LogOut,
  User,
  Shield,
  Plus,
  X,
  Check,
  Search,
  UserCheck,
} from 'react-feather';
import useSWR, { mutate } from 'swr';
import api, { fetcher } from '../../api/client';
import styles from './UserProfileModal.module.css';
import { toast } from 'react-hot-toast';

export default function UserProfileModal({ root }) {
  const [editingName, setEditingName] = useState(false);
  const [newName, setNewName] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [addingPermission, setAddingPermission] = useState(false);
  const [newPermission, setNewPermission] = useState({
    group_name: '',
    can_edit: false,
  });

  const { data: userData, error: userError } = useSWR(
    '/users/me',
    fetcher
  );
  const { data: allUsers } = useSWR(
    userData?.is_admin ? '/users' : null,
    fetcher
  );
  const { data: allGroups } = useSWR(
    userData?.is_admin ? '/recordings/groups' : null,
    fetcher
  );

  useEffect(() => {
    if (userData) {
      setNewName(userData.name || '');
    }
  }, [userData]);

  const handleSaveName = async () => {
    try {
      await api.patch('/users/me/name', { name: newName });
      await mutate('/users/me');
      setEditingName(false);
      toast.success('Имя обновлено');
    } catch (error) {
      toast.error('Ошибка при обновлении имени');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    window.location.href = '/login';
  };

  const handleUpdatePermission = async (
    userId,
    permissionId,
    permission
  ) => {
    try {
      await api.put(`/permissions/${permissionId}`, permission);
      await mutate('/users');
      toast.success('Права доступа обновлены');
    } catch (error) {
      toast.error('Ошибка при обновлении прав доступа');
    }
  };

  const handleAddPermission = async (userId) => {
    try {
      await api.post(`/permissions/users/${userId}`, newPermission);
      await mutate('/users');
      setAddingPermission(false);
      setNewPermission({ group_name: '', can_edit: false });
      toast.success('Права доступа добавлены');
    } catch (error) {
      if (error.response?.status === 400) {
        toast.error('Пользователь уже имеет доступ к этой группе');
      } else {
        toast.error('Ошибка при добавлении прав доступа');
      }
    }
  };

  const handleDeletePermission = async (permissionId) => {
    try {
      await api.delete(`/permissions/${permissionId}`);
      await mutate('/users');
      toast.success('Права доступа удалены');
    } catch (error) {
      toast.error('Ошибка при удалении прав доступа');
    }
  };

  const handleToggleAdmin = async (userId, isAdmin) => {
    try {
      await api.patch(`/users/${userId}/admin`, {
        is_admin: isAdmin,
      });
      await mutate('/users');
      toast.success(
        isAdmin
          ? 'Пользователь назначен администратором'
          : 'Пользователь больше не администратор'
      );
    } catch (error) {
      toast.error('Ошибка при изменении статуса администратора');
    }
  };

  const filteredUsers = allUsers?.filter(
    (user) =>
      user.username
        .toLowerCase()
        .includes(searchQuery.toLowerCase()) ||
      user.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Filter out groups that the user already has permissions for
  const getAvailableGroups = (user) => {
    if (!allGroups) return [];

    const userGroupNames = user.permissions.map((p) => p.group_name);
    return allGroups.filter(
      (group) => !userGroupNames.includes(group)
    );
  };

  return (
    <Modal
      root={root}
      title="Профиль пользователя"
      className={styles.modal}
    >
      <div className={styles.modalContent}>
        {/* Current User Section */}
        <div className={styles.userSection}>
          <div className={styles.userInfo}>
            <div className={styles.avatar}>
              <User size={24} />
            </div>
            <div className={styles.userDetails}>
              <div className={styles.username}>
                {userData?.username}
              </div>
              {editingName ? (
                <div className={styles.editNameContainer}>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className={styles.nameInput}
                    placeholder="Введите ваше имя"
                    autoFocus
                  />
                  <button
                    className={styles.actionButton}
                    onClick={handleSaveName}
                    aria-label="Сохранить имя"
                  >
                    <Save size={16} />
                  </button>
                </div>
              ) : (
                <div className={styles.nameRow}>
                  <span className={styles.name}>
                    {userData?.name || 'Добавить имя'}
                  </span>
                  <button
                    className={styles.actionButton}
                    onClick={() => setEditingName(true)}
                    aria-label="Редактировать имя"
                  >
                    <Edit2 size={16} />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Divider */}
        <hr className={styles.divider} />

        {/* Permissions Section - For regular users */}
        {!userData?.is_admin && (
          <div className={styles.permissionsSection}>
            <h3 className={styles.sectionTitle}>Доступные каналы</h3>
            {userData?.permissions?.length === 0 ? (
              <p className={styles.noPermissions}>
                У вас нет доступа ни к одной группе. Обратитесь к
                администратору для получения прав доступа.
              </p>
            ) : (
              <div className={styles.permissionsList}>
                {userData?.permissions?.map((permission) => (
                  <div
                    key={permission.id}
                    className={styles.permissionItem}
                  >
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
        )}

        {/* Admin Section */}
        {userData?.is_admin && (
          <div className={styles.adminSection}>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>
                Управление пользователями
              </h3>
            </div>

            <div className={styles.searchContainer}>
              <Search size={16} className={styles.searchIcon} />
              <input
                type="text"
                placeholder="Поиск пользователей..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={styles.searchInput}
              />
            </div>

            <div className={styles.usersList}>
              {filteredUsers?.map((user) => (
                <div key={user.id} className={styles.userCard}>
                  <div className={styles.userCardHeader}>
                    <div className={styles.userCardInfo}>
                      <div className={styles.userCardAvatar}>
                        <User size={16} />
                      </div>
                      <div className={styles.userCardDetails}>
                        <div className={styles.cardUsername}>
                          {user.username}
                        </div>
                        {user.name && (
                          <div className={styles.cardName}>
                            {user.name}
                          </div>
                        )}
                      </div>
                    </div>
                    {user.id !== userData.id && (
                      <button
                        className={`${styles.adminToggle} ${
                          user.is_admin ? styles.isAdmin : ''
                        }`}
                        onClick={() =>
                          handleToggleAdmin(user.id, !user.is_admin)
                        }
                      >
                        {user.is_admin
                          ? 'Администратор'
                          : 'Сделать администратором'}
                      </button>
                    )}
                  </div>

                  <div className={styles.userPermissions}>
                    <h4 className={styles.permissionsTitle}>
                      <UserCheck size={14} />
                      Доступ к каналам
                    </h4>

                    {user.permissions.length === 0 ? (
                      <p className={styles.noPermissions}>
                        У пользователя нет прав доступа
                      </p>
                    ) : (
                      <div className={styles.permissionItems}>
                        {user.permissions.map((permission) => (
                          <div
                            key={permission.id}
                            className={styles.permissionRow}
                          >
                            <span className={styles.groupName}>
                              {permission.group_name}
                            </span>
                            <div
                              className={styles.permissionControls}
                            >
                              <button
                                className={`${styles.editToggle} ${
                                  permission.can_edit
                                    ? styles.canEdit
                                    : ''
                                }`}
                                onClick={() =>
                                  handleUpdatePermission(
                                    user.id,
                                    permission.id,
                                    {
                                      ...permission,
                                      can_edit: !permission.can_edit,
                                    }
                                  )
                                }
                              >
                                {permission.can_edit
                                  ? 'Редактирование'
                                  : 'Только просмотр'}
                              </button>
                              <button
                                className={styles.deleteButton}
                                onClick={() =>
                                  handleDeletePermission(
                                    permission.id
                                  )
                                }
                                aria-label="Удалить доступ"
                              >
                                <X size={14} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {addingPermission && selectedUser === user.id ? (
                      <div className={styles.addPermissionForm}>
                        <select
                          value={newPermission.group_name}
                          onChange={(e) =>
                            setNewPermission({
                              ...newPermission,
                              group_name: e.target.value,
                            })
                          }
                          className={styles.groupSelect}
                        >
                          <option value="">Выберите группу...</option>
                          {getAvailableGroups(user).map((group) => (
                            <option key={group} value={group}>
                              {group}
                            </option>
                          ))}
                        </select>
                        <div className={styles.selectPermissionType}>
                          <button
                            className={`${
                              styles.permissionTypeButton
                            } ${
                              newPermission.can_edit
                                ? styles.active
                                : ''
                            }`}
                            onClick={() =>
                              setNewPermission({
                                ...newPermission,
                                can_edit: !newPermission.can_edit,
                              })
                            }
                          >
                            {newPermission.can_edit
                              ? 'Редактирование'
                              : 'Только просмотр'}
                          </button>
                        </div>
                        <div className={styles.formActions}>
                          <button
                            className={styles.saveButton}
                            onClick={() =>
                              handleAddPermission(user.id)
                            }
                            disabled={!newPermission.group_name}
                          >
                            Добавить
                          </button>
                          <button
                            className={styles.cancelButton}
                            onClick={() => {
                              setAddingPermission(false);
                              setSelectedUser(null);
                              setNewPermission({
                                group_name: '',
                                can_edit: false,
                              });
                            }}
                          >
                            Отмена
                          </button>
                        </div>
                      </div>
                    ) : (
                      getAvailableGroups(user).length > 0 && (
                        <button
                          className={styles.addButton}
                          onClick={() => {
                            setSelectedUser(user.id);
                            setAddingPermission(true);
                            setNewPermission({
                              group_name: '',
                              can_edit: false,
                            });
                          }}
                          disabled={
                            addingPermission &&
                            selectedUser === user.id
                          }
                        >
                          <Plus size={14} />
                          Добавить доступ
                        </button>
                      )
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Logout Button */}
        <button
          className={styles.logoutButton}
          onClick={handleLogout}
        >
          <LogOut size={16} />
          Выйти из системы
        </button>
      </div>
    </Modal>
  );
}
