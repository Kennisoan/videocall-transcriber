import React, { useState, useEffect } from 'react';
import Modal from '../Modal';
import TextInput from '../TextInput';
import api from '../../api/client';
import styles from './RecordCallModal.module.css';

import { Loader, Info, PhoneIncoming } from 'react-feather';

function RecordCallModal({ isOpen, onClose }) {
  const [meetLink, setMeetLink] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen === 'ready') {
      setMeetLink('');
      setIsSubmitted(false);
      setError('');
    }
  }, [isOpen]);

  const validateGoogleMeetLink = (link) => {
    const meetRegex = /^https:\/\/meet\.google\.com\/[a-z0-9-]+$/i;
    return meetRegex.test(link);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateGoogleMeetLink(meetLink)) {
      setError('Пожалуйста, введите корректную ссылку Google Meet');
      return;
    }

    setError('');

    try {
      const response = await api.post('/start_recording', {
        meet_url: meetLink,
      });
      setIsSubmitted(true);
    } catch (err) {
      console.error('Error starting recording:', err);
      setError(
        'Ошибка при запуске записи: ' +
          (err.response?.data?.detail || err.message)
      );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        setIsSubmitted(false);
        setError('');
        setMeetLink('');
      }}
      title="Записать звонок"
    >
      <h3 className={styles.title}>Звонок в Google Meet</h3>
      {isOpen === 'ready' && (
        <GoogleMeetForm
          meetLink={meetLink}
          setMeetLink={setMeetLink}
          isSubmitted={isSubmitted}
          error={error}
          handleSubmit={handleSubmit}
        />
      )}
      {isOpen !== 'ready' && <StatePill isOpen={isOpen} />}
      <hr className={styles.divider} />

      <h3 className={styles.title}>Huddle в Slack</h3>
      <p className={styles.description}>
        Начните huddle в Slack и бот присоединится и запишет ваш
        звонок автоматически.
      </p>
    </Modal>
  );
}

function GoogleMeetForm({
  meetLink,
  setMeetLink,
  isSubmitted,
  error,
  handleSubmit,
}) {
  return (
    <>
      <p className={styles.description}>
        Вставьте ссылку на звонок ниже, и бот присоединится и запишет
        ваш звонок:
      </p>
      <form onSubmit={handleSubmit}>
        <div className={styles.google_meet_input}>
          <TextInput
            value={meetLink}
            onChange={(e) => setMeetLink(e.target.value)}
            placeholder="https://meet.google.com/xxx-xxxx-xxx"
            disabled={isSubmitted}
          />
          <button
            type="submit"
            className={styles.google_meet_invite_button}
            disabled={!meetLink || isSubmitted}
          >
            Записать
          </button>
        </div>
      </form>
      {error && <p className={styles.error}>{error}</p>}
      {isSubmitted && (
        <p className={styles.success}>
          Бот присоединится к звонку в ближайшее время!
        </p>
      )}
    </>
  );
}

function StatePill({ isOpen }) {
  const verboseState = {
    waiting: 'Бот ожидает в лобби',
    joining: 'Присоединение к звонку',
    recording: 'Идёт запись звонка',
    processing: 'Обработка записи',
    unavailable: 'Запись звонков временно недоступна',
    initializing: 'Ещё пару секунд...',
  };

  const stateType = {
    waiting: 'info',
    joining: 'loading',
    recording: 'recording',
    processing: 'loading',
    unavailable: 'info',
    initializing: 'loading',
  };

  return (
    <div
      className={`${styles.state_pill} ${styles[stateType[isOpen]]}`}
    >
      {stateType[isOpen] === 'loading' ? (
        <Loader size={16} className={styles.loader} />
      ) : stateType[isOpen] === 'recording' ? (
        <PhoneIncoming className={styles.recording_icon} size={16} />
      ) : (
        <Info size={16} />
      )}
      {verboseState[isOpen]}
    </div>
  );
}

export default RecordCallModal;
