import React from 'react';

import styles from './Header.module.css';

function Header({ children, subtitle, trailing }) {
  return (
    <div className={styles.body}>
      <div className={styles.leading}>
        {children}
        {subtitle && children && (
          <>
            <span className={styles.separator}>∙</span>
            <span className={styles.subtitle}>{subtitle}</span>
          </>
        )}
      </div>
      {trailing && <div className={styles.trailing}>{trailing}</div>}
    </div>
  );
}

export default Header;
