import React, { useState } from 'react';
import Card from '../Card';
import LabeledText from '../LabeledText';
import ExpandableText from '../ExpandableText';
import Dropdown from '../Dropdown';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

import {
  MoreHorizontal,
  Headphones,
  FileText,
  Trash2,
} from 'react-feather';

import styles from './RecordingCard.module.css';

function formatRecordingName(created_at) {
  const date = parseISO(created_at);
  const formattedDate = format(date, "d MMMM 'в' HH:mm", {
    locale: ru,
  });
  return `Звонок ${formattedDate}`;
}

function handleDelete(recording) {
  console.log('Delete recording', recording);
  fetch(`http://localhost:8000/recordings/${recording.id}`, {
    method: 'DELETE',
  });
}

function RecordingCard({ recording }) {
  const formattedDate = formatRecordingName(recording.created_at);
  const source =
    recording.source === 'google_meet' ? 'Google Meet' : 'Slack';

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
          href={`http://localhost:8000/recordings/${recording.id}/audio`}
          className={styles.link}
        >
          <Headphones size={14} />
          {recording.filename}
        </a>
        <a
          href={`http://localhost:8000/recordings/${recording.id}/transcript`}
          className={styles.link}
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
