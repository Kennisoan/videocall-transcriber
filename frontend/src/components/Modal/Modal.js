import React, { useState, cloneElement } from 'react';
import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react';
import { X } from 'react-feather';
import styles from './Modal.module.css';

function Modal({
  root,
  title,
  children,
  footer,
  footerClassName,
  onClose,
  onOpen,
  isOpen: externalIsOpen,
  className,
}) {
  // Internal state for uncontrolled usage
  const [internalIsOpen, setInternalIsOpen] = useState(false);

  // Determine if we're in controlled or uncontrolled mode
  const isControlled = externalIsOpen !== undefined;
  const isOpen = isControlled ? externalIsOpen : internalIsOpen;

  const handleClose = () => {
    if (!isControlled) {
      setInternalIsOpen(false);
    }
    if (onClose) {
      onClose();
    }
  };

  const handleOpen = () => {
    if (!isControlled) {
      setInternalIsOpen(true);
    }
    if (onOpen) {
      onOpen();
    }
  };

  return (
    <>
      {root && cloneElement(root, { onClick: handleOpen })}

      <Dialog open={isOpen} onClose={handleClose}>
        <div className={styles.wrapper}>
          <DialogPanel
            className={`${styles.panel} ${className || ''}`}
          >
            {title && (
              <div className={styles.header}>
                <DialogTitle>{title}</DialogTitle>
                <button className={styles.x} onClick={handleClose}>
                  <X size={18} />
                </button>
              </div>
            )}

            <div className={styles.body}>
              {children}

              {footer && (
                <div
                  className={`${styles.footer} ${
                    footerClassName || ''
                  }`}
                >
                  {footer.map((element, index) =>
                    cloneElement(element, {
                      key: index,
                      onClick: (e) => {
                        element.props.onClick?.(e);
                        handleClose();
                      },
                    })
                  )}
                </div>
              )}
            </div>
          </DialogPanel>
        </div>
      </Dialog>
    </>
  );
}

export default Modal;
