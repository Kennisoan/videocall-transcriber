import React, { useState } from 'react';
import useSWR from 'swr';
import {
  parseISO,
  formatISO,
  isToday,
  isYesterday,
  isThisWeek,
} from 'date-fns';
import RecordingCard from '../RecordingCard';
import SlackRecordingCard from '../SlackRecordingCard';
import Container from '../Container';
import Header from '../Header';
import RecordCallModal from '../RecordCallModal/RecordCallModal';
import WhatsNew from '../WhatsNew';
import UserProfileModal from '../UserProfileModal';
import { Plus, Loader, ChevronDown, User } from 'react-feather';
import { fetcher } from '../../api/client';
import styles from './RecordingsList.module.css';

const CategorySection = ({ title, recordings }) => {
  if (recordings.length === 0) return null;

  return (
    <div className={styles.categorySection}>
      <h2 className={styles.categoryHeader}>{title}</h2>
      {recordings.map((recording) =>
        recording.source === 'slack' ? (
          <SlackRecordingCard
            key={recording.id}
            recording={recording}
          />
        ) : (
          <RecordingCard key={recording.id} recording={recording} />
        )
      )}
    </div>
  );
};

function RecordingsList({ state }) {
  const [showEarlier, setShowEarlier] = useState(false);
  const { data: recordings, error } = useSWR('/recordings', fetcher, {
    refreshInterval: 10000,
  });

  // Fetch user permissions to provide better feedback
  const { data: myPermissions } = useSWR('/permissions/my', fetcher);
  const { data: userData } = useSWR('/users/me', fetcher);

  const categorizeRecordings = (recordings) => {
    const categories = {
      today: [],
      yesterday: [],
      thisWeek: [],
      others: [],
    };

    recordings.forEach((recording) => {
      const date = parseISO(recording.created_at);
      if (isToday(date)) {
        categories.today.push(recording);
      } else if (isYesterday(date)) {
        categories.yesterday.push(recording);
      } else if (isThisWeek(date)) {
        categories.thisWeek.push(recording);
      } else {
        categories.others.push(recording);
      }
    });

    return categories;
  };

  if (error) return <div>Failed to load recordings</div>;
  if (!recordings)
    return (
      <div className={styles.loader_wrapper}>
        <Loader size={24} className={styles.loader} />
      </div>
    );

  const sortedRecordings = [...recordings]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .map((recording) => ({
      ...recording,
      created_at: formatISO(parseISO(recording.created_at), {
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }),
    }));

  const categories = categorizeRecordings(sortedRecordings);

  const hasEarlierRecordings =
    categories.yesterday.length > 0 ||
    categories.thisWeek.length > 0 ||
    categories.others.length > 0;

  const categoryConfig = [
    { key: 'today', title: 'Сегодня' },
    { key: 'yesterday', title: 'Вчера' },
    { key: 'thisWeek', title: 'На этой неделе' },
    { key: 'others', title: 'Ранее' },
  ];

  return (
    <Container className={styles.wrapper}>
      <Header
        trailing={
          <div className={styles.headerControls}>
            <UserProfileModal
              root={
                <button className={styles.profileButton}>
                  <div className={styles.avatarCircle}>
                    <User size={14} strokeWidth={2} />
                  </div>
                  {userData?.name
                    ? userData.name
                    : userData?.username || 'Профиль'}
                </button>
              }
            />
            <RecordCallModal
              state={state}
              root={
                <button className={styles.newRecordingButton}>
                  <Plus size={14} strokeWidth={2.3} />
                  Записать звонок
                </button>
              }
            />
          </div>
        }
      >
        Записи звонков
      </Header>
      <div className={styles.recordings}>
        <WhatsNew />
        {sortedRecordings.length === 0 ? (
          <div className={styles.placeholder}>
            {myPermissions && myPermissions.length === 0
              ? 'У вас нет доступа к записям. Обратитесь к администратору для получения прав доступа.'
              : 'Нет записей звонков.'}
          </div>
        ) : (
          <>
            <CategorySection
              key="today"
              title="Сегодня"
              recordings={categories.today}
            />
            {categories.today.length === 0 && !showEarlier && (
              <div className={styles.placeholder}>
                Сегодня нет записей.
              </div>
            )}
            {hasEarlierRecordings && (
              <div className={styles.earlierSection}>
                {!showEarlier ? (
                  <button
                    className={styles.showEarlierButton}
                    onClick={() => setShowEarlier(true)}
                  >
                    <ChevronDown size={16} />
                    Показать более ранние записи
                  </button>
                ) : (
                  <div className={styles.earlierRecordings}>
                    {categoryConfig.slice(1).map(({ key, title }) => (
                      <CategorySection
                        key={key}
                        title={title}
                        recordings={categories[key]}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </Container>
  );
}

export default RecordingsList;
