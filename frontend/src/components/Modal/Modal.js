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
}) {
  const [isOpen, setIsOpen] = useState(false);

  const closeModal = () => {
    setIsOpen(false);
    onClose?.();
  };

  return (
    <>
      {cloneElement(root, { onClick: () => setIsOpen(true) })}

      <Dialog open={isOpen} onClose={closeModal}>
        <div className={styles.wrapper}>
          <DialogPanel className={styles.panel}>
            <div className={styles.header}>
              <DialogTitle>{title}</DialogTitle>
              <button className={styles.x} onClick={closeModal}>
                <X size={18} />
              </button>
            </div>

            <div className={styles.body}>
              {children}

              {footer && (
                <div
                  className={`${styles.footer} ${footerClassName}`}
                >
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
          </DialogPanel>
        </div>
      </Dialog>
    </>
  );
}

export default Modal;
