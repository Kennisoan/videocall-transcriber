import React, { useState, useRef, useEffect } from 'react';
import { ChevronUp, ChevronDown } from 'react-feather';

import styles from './ExpandableText.module.css';

function ExpandableText({ text, lines = 3 }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClampable, setIsClampable] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    const content = contentRef.current;
    if (!content) return;

    const checkClampable = () => {
      const lineHeight = parseInt(
        getComputedStyle(content).lineHeight
      );
      const maxHeight = lineHeight * lines;
      setIsClampable(content.scrollHeight > maxHeight + 1);
    };

    checkClampable();
    window.addEventListener('resize', checkClampable);
    return () => window.removeEventListener('resize', checkClampable);
  }, [text, lines]);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const contentStyle = {
    maxHeight: isExpanded ? 'unset' : `calc(1.4em * ${lines})`,
    WebkitLineClamp: isExpanded ? 'unset' : lines,
  };

  return (
    <div className={styles.wrapper}>
      <div
        ref={contentRef}
        className={styles.content}
        style={contentStyle}
      >
        {text}
      </div>
      {isClampable && (
        <button onClick={toggleExpanded} className={styles.toggle}>
          {isExpanded ? (
            <>
              Скрыть
              <ChevronUp size={18} strokeWidth={1.75} />
            </>
          ) : (
            <>
              Показать полностью
              <ChevronDown size={18} strokeWidth={1.75} />
            </>
          )}
        </button>
      )}
    </div>
  );
}

export default ExpandableText;
