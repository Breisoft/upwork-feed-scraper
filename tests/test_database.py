import os
import unittest
from unittest.mock import patch, MagicMock
from typing import List

import datetime

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from custom_exceptions import MissingCredentialsException

from database import Base, RSSFeed, RSSFeedEntry, Database

def get_time(time_str: str) -> datetime:
    return datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.test_db_path = 'test.db'
        engine = create_engine(f'sqlite:///{self.test_db_path}')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        os.remove(self.test_db_path)

    @patch.dict(os.environ, {'SQLITE_PATH': 'test.db'})
    def test_init(self):
        db = Database()
        self.assertEqual(db._path, self.test_db_path)

    def test_init_no_sqlite_path(self):
        with self.assertRaises(MissingCredentialsException):
            with patch.dict(os.environ):
                del os.environ['SQLITE_PATH']
                db = Database()

    def test_commit(self):
        with patch.object(self.session, 'commit') as mock_commit:
            db = Database()
            db._session = self.session
            db._commit()
            mock_commit.assert_called_once()

    def test_get_all_feeds(self):
        db = Database()
        db._session = self.session
        self.session.add(RSSFeed(url='https://example.com/rss'))
        self.session.commit()

        feeds = db.get_all_feeds()
        self.assertEqual(len(feeds), 1)
        self.assertEqual(feeds[0].url, 'https://example.com/rss')

    def test_get_all_feed_entries(self):
        db = Database()
        db._session = self.session
        feed = RSSFeed(url='https://example.com/rss')
        self.session.add(feed)
        self.session.commit()

        entry = RSSFeedEntry(
            url='https://example.com/rss/entry1',
            title='Entry 1',
            posted_on_timestamp=get_time('2022-01-01 00:00:00'),
            rss_feed_id=feed.id
        )
        self.session.add(entry)
        self.session.commit()

        entries = db.get_all_feed_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].url, 'https://example.com/rss/entry1')

    def test_insert_entries(self):
        db = Database()
        db._session = self.session
        feed = RSSFeed(url='https://example.com/rss')
        self.session.add(feed)
        self.session.commit()

        entries = [
            RSSFeedEntry(
                url='https://example.com/rss/entry1',
                title='Entry 1',
                posted_on_timestamp=get_time('2022-01-01 00:00:00'),
                rss_feed_id=feed.id
            ),
            RSSFeedEntry(
                url='https://example.com/rss/entry2',
                title='Entry 2',
                posted_on_timestamp=get_time('2022-01-02 00:00:00'),
                rss_feed_id=feed.id
            ),
        ]
        db.insert_entries(entries)

        results = self.session.query(RSSFeedEntry).all()
        self.assertEqual(len(results), 2)

    def test_update_entries_emailed(self):
        db = Database()
        db._session = self.session
        feed = RSSFeed(url='https://example.com/rss')
        self.session.add(feed)
        self.session.commit()

        entry = RSSFeedEntry(
            url='https://example.com/rss/entry1',
            title='Entry 1',
            posted_on_timestamp=get_time('2022-01-01 00:00:00'),
            emailed=False,
            rss_feed_id=feed.id
        )
        self.session.add(entry)
        self.session.commit()

        db.update_entries_emailed([entry])

        updated_entry = self.session.query(RSSFeedEntry).filter(RSSFeedEntry.id == entry.id).one()
        self.assertEqual(updated_entry.emailed, True)

if __name__ == '__main__':
    unittest.main()

