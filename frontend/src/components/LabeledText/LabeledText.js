import React from 'react';

import styles from './LabeledText.module.css';

function LabeledText({ children, label, className }) {
  return (
    <div className={styles.detail}>
      <div className={styles.detail_label}>{label}</div>
      <div className={className}>{children}</div>
    </div>
  );
}

export default LabeledText;
