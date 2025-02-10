import React, { useState } from 'react';
import useSWR from 'swr';
import { parseISO, formatISO } from 'date-fns';
import RecordingCard from '../RecordingCard';
import Container from '../Container';
import Header from '../Header';
import RecordCallModal from '../RecordCallModal/RecordCallModal';
import { Plus } from 'react-feather';
import { fetcher } from '../../api/client';
import styles from './RecordingsList.module.css';

function RecordingsList() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: recordings, error } = useSWR('/recordings', fetcher);

  if (error) return <div>Failed to load recordings</div>;
  if (!recordings) return <div>Loading...</div>;

  const sortedRecordings = [...recordings]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .map((recording) => ({
      ...recording,
      created_at: formatISO(parseISO(recording.created_at), {
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }),
    }));

  return (
    <Container className={styles.wrapper}>
      <Header
        trailing={
          <button
            className={styles.newRecordingButton}
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={14} strokeWidth={2.3} />
            Записать звонок
          </button>
        }
      >
        Записи звонков
      </Header>
      <div className={styles.recordings}>
        {sortedRecordings.length === 0 ? (
          <div className={styles.placeholder}>
            Нет записей звонков.
          </div>
        ) : (
          sortedRecordings.map((recording) => (
            <RecordingCard key={recording.id} recording={recording} />
          ))
        )}
      </div>
      <RecordCallModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        root={
          <button
            className={styles.newRecordingButton}
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={14} strokeWidth={2.3} />
            Записать звонок
          </button>
        }
      />
    </Container>
  );
}

export default RecordingsList;
