import React, { useState, useMemo } from 'react';
import LargeModal from '../LargeModal';
import api from '../../api/client';
import styles from './Transcript.module.css';
import { Loader } from 'react-feather';
// Pre-defined colors for speakers
const SPEAKER_COLORS = ['#007AFF', '#35A651', '#9626FF', '#00A9A2'];

function TranscriptMessage({ message, speaker, color }) {
  const formatTime = (dateString) => {
    const date = new Date(dateString.replace(/Z$/, ''));
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Create a default speaker object for unknown speakers
  const defaultSpeaker = {
    name: 'Неопознанный ковбой',
    profile_pic: 'https://i.pravatar.cc/150?img=65',
  };

  // Use the provided speaker info or fall back to default
  const speakerInfo = speaker || defaultSpeaker;

  return (
    <div className={styles.messageContainer}>
      <img
        src={speakerInfo.profile_pic}
        alt={speakerInfo.name}
        className={styles.avatar}
      />
      <div className={styles.messageContent}>
        <div className={styles.messageHeader}>
          <span className={styles.username} style={{ color }}>
            {speakerInfo.name}
          </span>
          <span className={styles.timestamp}>
            {formatTime(message.start)}
          </span>
        </div>
        <div className={styles.messageText}>{message.text}</div>
      </div>
    </div>
  );
}

function Transcript({ recording, root, title }) {
  const [recordingData, setRecordingData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Update speakerColors to include 'unknown' speaker
  const speakerColors = useMemo(() => {
    if (!recordingData?.speakers) return {};

    const colors = {};
    // First assign colors to known speakers
    Object.keys(recordingData.speakers).forEach((speaker, index) => {
      colors[speaker] = SPEAKER_COLORS[index % SPEAKER_COLORS.length];
    });
    // Add a color for unknown speaker
    colors['unknown'] = '#808080'; // Gray color for unknown speakers
    return colors;
  }, [recordingData?.speakers]);

  const sortedTranscript = useMemo(() => {
    if (!recordingData?.diarized_transcript) return [];

    return [...recordingData.diarized_transcript].sort(
      (a, b) => new Date(a.start) - new Date(b.start)
    );
  }, [recordingData?.diarized_transcript]);

  const fetchTranscript = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get(`/recordings/${recording.id}`);
      setRecordingData(response.data);
    } catch (err) {
      setError('Failed to load transcript');
      console.error('Error fetching transcript:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LargeModal root={root} title={title} onOpen={fetchTranscript}>
      <div className={styles.content}>
        {isLoading ? (
          <div className={styles.loader_wrapper}>
            <Loader size={24} className={styles.loader} />
          </div>
        ) : error ? (
          <div className={styles.error}>{error}</div>
        ) : (
          <div className={styles.transcriptContainer}>
            {sortedTranscript.map((message, index) => (
              <TranscriptMessage
                key={`${message.start}-${index}`}
                message={message}
                speaker={recordingData.speakers[message.speaker]}
                color={speakerColors[message.speaker]}
              />
            ))}
          </div>
        )}
      </div>
    </LargeModal>
  );
}

export default Transcript;
