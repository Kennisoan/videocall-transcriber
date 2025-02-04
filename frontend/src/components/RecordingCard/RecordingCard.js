import React from 'react';
import Card from '../Card';
import LabeledText from '../LabeledText';
import ExpandableText from '../ExpandableText';
import Dropdown from '../Dropdown';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';
import axios from 'axios';
import {
  MoreHorizontal,
  Headphones,
  FileText,
  Trash2,
} from 'react-feather';

import styles from './RecordingCard.module.css';

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

function formatRecordingName(created_at) {
  const date = parseISO(created_at);
  const formattedDate = format(date, "d MMMM 'в' HH:mm", {
    locale: ru,
  });
  return `Звонок ${formattedDate}`;
}

async function handleDelete(recording) {
  try {
    await api.delete(`/recordings/${recording.id}`);
    // Force reload the recordings list
    window.location.reload();
  } catch (error) {
    console.error('Error deleting recording:', error);
  }
}

async function downloadFile(url, filename) {
  try {
    const response = await api.get(url, {
      responseType: 'blob',
    });

    // Create a blob from the response data
    const blob = new Blob([response.data]);

    // Create a link element and trigger download
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Error downloading file:', error);
  }
}

function RecordingCard({ recording }) {
  const formattedDate = formatRecordingName(recording.created_at);
  const source =
    recording.source === 'google_meet' ? 'Google Meet' : 'Slack';

  const handleAudioDownload = () => {
    downloadFile(
      `/recordings/${recording.id}/audio`,
      recording.filename
    );
  };

  const handleTranscriptDownload = () => {
    downloadFile(
      `/recordings/${recording.id}/transcript`,
      recording.filename.replace('.wav', '.txt')
    );
  };

  return (
    <Card className={styles.card}>
      {/* Card Header */}
      <div className={styles.header}>
        <div className={styles.title}>
          {formattedDate}
          <span className={styles.title_separator}>∙</span>
          <span className={styles.title_secondary}>{source}</span>
        </div>
        <div className={styles.controls}>
          <Dropdown
            trigger={<HeaderButton icon={<MoreHorizontal />} />}
            items={[
              {
                label: (
                  <div
                    style={{
                      color: '#ff424d',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <Trash2 size={18} />
                    <p>Удалить запись</p>
                  </div>
                ),
                onClick: () => handleDelete(recording),
              },
            ]}
          />
        </div>
      </div>

      {/* Details */}
      <LabeledText label="Транскрипция">
        <ExpandableText text={recording.transcript} />
      </LabeledText>
      <LabeledText label="Материалы">
        <a
          href="#"
          className={styles.link}
          onClick={(e) => {
            e.preventDefault();
            handleAudioDownload();
          }}
        >
          <Headphones size={14} />
          {recording.filename}
        </a>
        <a
          href="#"
          className={styles.link}
          onClick={(e) => {
            e.preventDefault();
            handleTranscriptDownload();
          }}
        >
          <FileText size={14} />
          {recording.filename.replace('.wav', '.txt')}
        </a>
      </LabeledText>
    </Card>
  );
}

function HeaderButton({ icon, onClick, size = 18, disabled }) {
  return (
    <button
      onClick={onClick}
      className={styles.header_button}
      disabled={disabled}
    >
      {React.cloneElement(icon, { ...icon.props, size })}
    </button>
  );
}

export default RecordingCard;
