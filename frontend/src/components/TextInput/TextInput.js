import React, { useRef, useEffect } from 'react';

import styles from './TextInput.module.css';

function TextInput({ id, label, value, hint, ...delegated }) {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  return (
    <div className={styles.wrapper}>
      {label && (
        <label className={styles.label} htmlFor={id}>
          {label}
        </label>
      )}
      <textarea
        value={value || ''}
        ref={textareaRef}
        className={styles.input}
        rows={1}
        id={id}
        spellCheck="false"
        aria-describedby={`${id}-description`}
        {...delegated}
      />
      {/* <p id={`${id}-description`} hidden>
        {label}
      </p> */}
      {hint && <p className={styles.hint}>{hint}</p>}
    </div>
  );
}

export default TextInput;
