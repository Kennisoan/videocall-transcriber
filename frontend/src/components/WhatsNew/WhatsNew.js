import React, { useState, useEffect } from 'react';
import { Star } from 'react-feather';
import styles from './WhatsNew.module.css';

// Change this version number when adding new features
const CURRENT_VERSION = '1.1.1';
const STORAGE_KEY = 'app_version';

const WhatsNew = () => {
  const [isVisible, setIsVisible] = useState(false);

  const newFeatures = [
    'Транскрибация звонков через ElevenLabs',
    'Гораздо более качественное определение говорящего, с точностью до слова',
  ];

  useEffect(() => {
    // Check if we should show the what's new component
    const storedVersion = localStorage.getItem(STORAGE_KEY);

    if (!storedVersion || storedVersion !== CURRENT_VERSION) {
      setIsVisible(true);
    }
  }, []);

  const handleDismiss = () => {
    // Update the version in localStorage
    localStorage.setItem(STORAGE_KEY, CURRENT_VERSION);
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className={styles.whatsNewContainer}>
      <div className={styles.iconContainer}>
        <Star size={18} className={styles.sparkleIcon} />
      </div>
      <div className={styles.contentContainer}>
        <h3 className={styles.title}>Что нового</h3>
        {newFeatures.length > 0 && (
          <ul className={styles.featuresList}>
            {newFeatures.map((feature, index) => (
              <li key={index} className={styles.featureItem}>
                {feature}
              </li>
            ))}
          </ul>
        )}
      </div>
      <button
        className={styles.dismissButton}
        onClick={handleDismiss}
        aria-label="Закрыть"
      >
        ✕
      </button>
    </div>
  );
};

export default WhatsNew;
