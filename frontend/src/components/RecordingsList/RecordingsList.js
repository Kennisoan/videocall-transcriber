import React from 'react';
import useSWR from 'swr';

import { parseISO, formatISO } from 'date-fns';

const fetcher = (...args) => fetch(...args).then((res) => res.json());

import RecordingCard from '../RecordingCard';
import Container from '../Container';
import Header from '../Header';
import { Plus } from 'react-feather';

import styles from './RecordingsList.module.css';

function RecordingsList() {
  const { data: recordings, error } = useSWR(
    'http://localhost:8000/recordings/',
    fetcher,
    {
      refreshInterval: 5000,
    }
  );

  if (error) return <div>Ошибка загрузки записей</div>;
  if (!recordings) return <div>Загрузка...</div>;

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
      <Header trailing={<NewRecordingButton />}>
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
    </Container>
  );
}

function NewRecordingButton() {
  return (
    <button className={styles.newRecordingButton}>
      <Plus size={14} strokeWidth={2.3} />
      Записать звонок
    </button>
  );
}

export default RecordingsList;
