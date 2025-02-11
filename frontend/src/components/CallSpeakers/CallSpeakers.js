import React from 'react';
import styles from './CallSpeakers.module.css';

function CallSpeakers({ speakers }) {
  const speakersArray = Object.values(speakers);
  const sortedSpeakers = speakersArray.sort(
    (a, b) => b.duration - a.duration
  );
  const topSpeakers = sortedSpeakers.slice(0, 3);
  const extraCount = sortedSpeakers.length - topSpeakers.length;

  return (
    <div className={styles.callSpeakers}>
      {topSpeakers.map((speaker) => (
        <img
          key={speaker.name}
          src={speaker.profile_pic}
          alt={speaker.name}
          className={styles.avatar}
        />
      ))}
      {extraCount > 0 && (
        <div className={styles.extraAvatar}>+{extraCount}</div>
      )}
    </div>
  );
}

export default CallSpeakers;
