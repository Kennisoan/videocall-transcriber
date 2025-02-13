import React, { useState, cloneElement } from 'react';
import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react';
import { X } from 'react-feather';
import styles from './LargeModal.module.css';

function LargeModal({
  root,
  title,
  children,
  footer,
  footerClassName,
  onClose,
  onOpen,
}) {
  const [isOpen, setIsOpen] = useState(false);

  const closeModal = () => {
    setIsOpen(false);
    onClose?.();
  };

  const openModal = () => {
    setIsOpen(true);
    onOpen?.();
  };

  return (
    <>
      {cloneElement(root, { onClick: openModal })}

      <Dialog
        open={isOpen}
        onClose={closeModal}
        className={styles.dialog}
      >
        <div className={styles.wrapper}>
          <div className={styles.panel}>
            <div className={styles.header}>
              <DialogTitle>{title}</DialogTitle>
              <button className={styles.x} onClick={closeModal}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.body}>{children}</div>

            {footer && (
              <div className={`${styles.footer} ${footerClassName}`}>
                {footer.map((element, index) =>
                  cloneElement(element, {
                    key: index,
                    onClick: (e) => {
                      element.props.onClick?.(e);
                      closeModal();
                    },
                  })
                )}
              </div>
            )}
          </div>
        </div>
      </Dialog>
    </>
  );
}

export default LargeModal;
