import React from 'react';

import styles from './Card.module.css';

function Card({ children, className, ...delegated }) {
  return (
    <div
      className={`${styles.wrapper} ${className || ''}`.trim()}
      {...delegated}
    >
      {children}
    </div>
  );
}

export default Card;
