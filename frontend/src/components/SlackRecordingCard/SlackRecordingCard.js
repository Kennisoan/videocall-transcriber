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
  Download,
  Hash,
  Clock,
} from 'react-feather';

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
    window.open(`${api.defaults.baseURL}${url}`);
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

  const diarizedTranscriptString = recording.diarized_transcript
    ? recording.diarized_transcript
        .map((segment) => `— ${segment.text}`)
        .join('\n')
    : 'Не удалось создать транскрипцию.';

  return (
    <Card className={styles.card}>
      {/* Card Header */}
      <div className={styles.header}>
        <div className={styles.title}>
          {formattedDate}
          <span className={styles.title_separator}>∙</span>
          <HeaderIcon name={recording.source} />
          <span className={styles.title_secondary}>{source}</span>
        </div>
        <div className={styles.controls}>
          <HeaderDropdown recording={recording} />
        </div>
      </div>

      {/* Details */}
      <LabeledText label="Транскрипция">
        <ExpandableText
          text={
            diarizedTranscriptString ||
            'Не удалось создать транскрипцию.'
          }
        />
      </LabeledText>

      {/* Footer */}
      <div className={styles.footer}>
        <LabeledText label="Участники">
          <CallSpeakers speakers={recording.speakers} />
        </LabeledText>
        <LabeledText label="Канал">
          <div className={styles.footer_info}>
            <Hash size={16} strokeWidth={3} />
            <span>{recording.meeting_name || 'Не определён'}</span>
          </div>
        </LabeledText>
        <LabeledText label="Продолжительность">
          <div className={styles.footer_info}>
            <Clock size={16} strokeWidth={3} />
            <span>{recording.duration || 'Не определена'}</span>
          </div>
        </LabeledText>
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
              <Download size={18} />
              <p>Скачать аудио</p>
            </>
          ),
          onClick: () => handleAudioDownload(recording),
        },
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

export default SlackRecordingCard;
