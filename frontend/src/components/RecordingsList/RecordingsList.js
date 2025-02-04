import React from 'react';
import useSWR from 'swr';
import { parseISO, formatISO } from 'date-fns';
import RecordingCard from '../RecordingCard';
import Container from '../Container';
import Header from '../Header';
import RecordCallModal from '../RecordCallModal/RecordCallModal';
import { Plus } from 'react-feather';
import axios from 'axios';
import styles from './RecordingsList.module.css';

// Create axios instance with auth token
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers['x-token'] = token;
  }
  return config;
});

// Custom fetcher using axios
const fetcher = (url) => api.get(url).then((res) => res.data);

function RecordingsList() {
  const { data: recordings, error } = useSWR(
    '/recordings/',
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
    <RecordCallModal
      as={
        <button className={styles.newRecordingButton}>
          <Plus size={14} strokeWidth={2.3} />
          Записать звонок
        </button>
      }
    />
  );
}

export default RecordingsList;
