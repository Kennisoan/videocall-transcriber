import React from 'react';
import Card from '../Card';
import LabeledText from '../LabeledText';
import ExpandableText from '../ExpandableText';
import Dropdown from '../Dropdown';
import CallSpeakers from '../CallSpeakers';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';
import api from '../../api/client';
import {
  MoreHorizontal,
  Headphones,
  FileText,
  Trash2,
  Hash,
  Clock,
} from 'react-feather';
import Transcript from '../Transcript';

import styles from './SlackRecordingCard.module.css';

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
    const token = localStorage.getItem('authToken');
    const response = await fetch(`${api.defaults.baseURL}${url}`, {
      headers: {
        'x-token': token,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Create a blob from the response
    const blob = await response.blob();

    // Create a link and trigger download
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Error downloading file:', error);
  }
}

function SlackRecordingCard({ recording }) {
  const formattedDate = formatRecordingName(recording.created_at);
  const source = 'Slack';

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
          <HeaderIcon name={recording.source} />
          <span className={styles.title_secondary}>
            {recording.meeting_name || 'Не определён'}
          </span>
        </div>
        <div className={styles.controls}>
          <HeaderDropdown recording={recording} />
        </div>
      </div>

      {/* TLDR */}
      {recording.tldr && (
        <LabeledText label="О чём был звонок">
          <ExpandableText text={recording.tldr} lines={2} />
        </LabeledText>
      )}

      {/* Footer */}
      <div className={styles.footer}>
        <LabeledText label="Участники">
          <CallSpeakers speakers={recording.speakers} />
        </LabeledText>
        <LabeledText label="Продолжительность">
          <div className={styles.footer_info}>
            <Clock size={16} strokeWidth={3} />
            <span>
              {formatDuration(recording.duration) || 'Не определена'}
            </span>
          </div>
        </LabeledText>
      </div>

      {/* Actions */}
      <div className={styles.actions}>
        <Transcript
          recording={recording}
          title={formattedDate}
          root={
            <button className={styles.action_button}>
              <FileText size={16} />
              Транскрипция
            </button>
          }
        />
        <button
          className={`${styles.action_button} ${styles.action_button_audio}`}
          onClick={handleAudioDownload}
        >
          <Headphones size={16} />
          Аудио
        </button>
      </div>
    </Card>
  );
}

function HeaderIcon({ name }) {
  const size = 16;

  return (
    <img
      width={size}
      height={size}
      className={styles.header_icon}
      src={`/assets/img/${name}.svg`}
    />
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

function HeaderDropdown({ recording }) {
  return (
    <Dropdown
      trigger={<HeaderButton icon={<MoreHorizontal />} />}
      items={[
        {
          label: (
            <>
              <Trash2 size={18} color="#ff424d" />
              <p style={{ color: '#ff424d' }}>Удалить запись</p>
            </>
          ),
          onClick: () => handleDelete(recording),
        },
      ]}
    />
  );
}

function formatDuration(duration) {
  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  const seconds = duration % 60;

  if (hours > 0) {
    return `${hours} час ${minutes} мин`;
  } else if (minutes > 0) {
    return `${minutes} мин ${seconds} сек`;
  } else if (seconds > 0) {
    return `${seconds} сек`;
  } else {
    return 'Не определена';
  }
}

export default SlackRecordingCard;
