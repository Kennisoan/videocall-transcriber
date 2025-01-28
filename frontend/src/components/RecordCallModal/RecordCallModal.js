import React, { useState } from 'react';
import Modal from '../Modal';
import TextInput from '../TextInput';

import styles from './RecordCallModal.module.css';

function RecordCallModal({ as }) {
  const [meetLink, setMeetLink] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  const validateGoogleMeetLink = (link) => {
    const meetRegex = /^https:\/\/meet\.google\.com\/[a-z0-9-]+$/i;
    return meetRegex.test(link);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validateGoogleMeetLink(meetLink)) {
      setError('Пожалуйста, введите корректную ссылку Google Meet');
      return;
    }

    setIsSubmitted(true);
    setError('');
    // Make an API call to handle the meet link
  };

  return (
    <Modal root={as} title="Записать звонок">
      <h3 className={styles.title}>Звонок в Google Meet</h3>
      <p className={styles.description}>
        Вставьте ссылку на звонок ниже, и бот присоединится и запишет
        ваш звонок:
      </p>
      <form onSubmit={handleSubmit}>
        <div className={styles.google_meet_input}>
          <TextInput
            value={meetLink}
            onChange={(e) => setMeetLink(e.target.value)}
            placeholder="https://meet.google.com/xxx-xxx-xxx"
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
      <hr className={styles.divider} />
      <h3 className={styles.title}>Huddle в Slack</h3>
      <p className={styles.description}>
        Начните huddle в Slack и бот присоединится и запишет ваш
        звонок автоматически.
      </p>
    </Modal>
  );
}

export default RecordCallModal;
