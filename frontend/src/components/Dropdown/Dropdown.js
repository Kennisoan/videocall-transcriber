import React from 'react';

import {
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
} from '@headlessui/react';

import styles from './Dropdown.module.css';

function Dropdown({ trigger, items }) {
  return (
    <Menu as="div" className={styles.dropdown}>
      <MenuButton as="div" className={styles.trigger}>
        {trigger}
      </MenuButton>
      <MenuItems className={styles.menu}>
        {items.map((item, index) => (
          <MenuItem key={index}>
            {({ active }) => (
              <button
                className={`${styles.item} ${
                  active ? styles.active : ''
                }`}
                onClick={item.onClick}
              >
                {item.label}
              </button>
            )}
          </MenuItem>
        ))}
      </MenuItems>
    </Menu>
  );
}

export default Dropdown;
