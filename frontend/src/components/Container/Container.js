import React from 'react';

import styles from './Container.module.css';

function Container({ children, className, ...delegated }, ref) {
  return (
    <div
      className={`${styles.wrapper} ${className || ''}`.trim()}
      {...delegated}
      ref={ref}
    >
      {children}
    </div>
  );
}

export default React.forwardRef(Container);
