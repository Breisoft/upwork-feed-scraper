import os
import datetime
from typing import List

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy import DateTime, ForeignKey, Text, Boolean, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from custom_exceptions import MissingCredentialsException

Base = declarative_base()

class RSSFeed(Base):
    """
    Represents an RSS feed as a SQL Alchemy ORM class.

    Args:
        id: An Integer representing a unique primary key.
        url: A String that represents the unique URL of the RSS feed.
        last_checked_timestamp: A DateTime representing the last time the feed was checked.
        feed_entries: A relationship with RSSFeedEntry class, represents the entries of the RSS feed.

    Raises:
        AttributeError: If the given argument types do not match the expected types.
    """
    __tablename__ = 'rss_feed'
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    last_checked_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    feed_entries = relationship("RSSFeedEntry", back_populates="rss_feed")


class RSSFeedEntry(Base):
    """
    Represents an RSS feed entry as a SQL Alchemy ORM class.

    Args:
        id: An Integer representing a unique primary key.
        url: A String that represents the unique URL of the RSS feed entry.
        title: A String representing the title of the entry.
        posted_on_timestamp: A DateTime indicating when the entry was posted.
        low_hourly: A String indicating the low hourly rate for a job (optional).
        high_hourly: A String indicating the high hourly rate for a job (optional).
        skills: A Text indicating the required skills for a job (optional).
        keywords: A Text indicating the keywords for the job (optional).
        emailed: A Boolean indicating whether the entry has been emailed.
        rss_feed_id: An Integer foreign key representing the associated RSS feed.
        rss_feed: A relationship with RSSFeed class, representing the associated RSS feed.

    Raises:
        AttributeError: If the given argument types do not match the expected types.
    """
    __tablename__ = 'rss_feed_entry'
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    posted_on_timestamp = Column(DateTime, nullable=False)
    low_hourly = Column(String, nullable=True)
    high_hourly = Column(String, nullable=True)
    skills = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    emailed = Column(Boolean, nullable=False, default=False)
    rss_feed_id = Column(Integer, ForeignKey('rss_feed.id'), nullable=False)
    rss_feed = relationship("RSSFeed", back_populates="feed_entries")


class Database():
    """
    Represents a Database interface for the RSS Feed and RSS Feed Entries.

    Args:
        _path: A String path to the SQLite database.
        _engine: A SQLAlchemy engine instance.
        _session: A SQLAlchemy session instance.

    Raises:
        MissingCredentialsException: If the SQLITE_PATH is not set in .env.
        AttributeError: If the given argument types do not match the expected types.
    """

    def __init__(self):

        try:
            self._path = os.environ['SQLITE_PATH']
        except KeyError as exc:
            raise MissingCredentialsException(
                'SQLITE_PATH credential not set in .env!') from exc

         # Create an SQLite engine
        self._engine = create_engine(f'sqlite:///{self._path}')

        Base.metadata.create_all(self._engine)

        Session = sessionmaker(bind=self._engine)

        self._session = Session()

    def _commit(self):
        """
        Commits the current transaction to the database.

        Raises:
            SQLAlchemyError: If there is an error committing the transaction.
        """
        self._session.commit()

    def get_all_feeds(self) -> List[RSSFeed]:
        """
        Retrieves all RSS feeds from the database.

        Returns:
            A list of all RSSFeed objects.

        Raises:
            SQLAlchemyError: If there is an error querying the database.
        """
        feeds = self._session.query(RSSFeed).all()
        return feeds

    def get_all_feed_entries(self) -> List[RSSFeedEntry]:
        """
        Retrieves all RSS feed entries from the database.

        Returns:
            A list of all RSSFeedEntry objects.

        Raises:
            SQLAlchemyError: If there is an error querying the database.
        """
        feed_entries = self._session.query(RSSFeedEntry).all()
        return feed_entries

    def insert_entries(self, entries: List[RSSFeedEntry]):
        """
        Inserts multiple RSS feed entries into the database.

        Args:
            entries: A list of RSSFeedEntry objects to be inserted.

        Raises:
            SQLAlchemyError: If there is an error adding the entries.
        """
        for entry in entries:
            self._session.add(entry)
        self._commit()

    def update_entries_emailed(self, entries: List[RSSFeedEntry]):
        """
        Marks multiple RSS feed entries as emailed in the database.

        Args:
            entries: A list of RSSFeedEntry objects to be updated.

        Raises:
            SQLAlchemyError: If there is an error updating the entries.
        """
        for entry in entries:
            entry.emailed = True
        self._commit()

    def get_unemailed_entries(self) -> List[RSSFeedEntry]:
        """
        Retrieves all RSS feed entries from the database that have not been emailed.

        Returns:
            A list of RSSFeedEntry objects that have not been emailed.

        Raises:
            SQLAlchemyError: If there is an error querying the database.
        """
        unemailed_entries = self._session.query(RSSFeedEntry).filter(
            RSSFeedEntry.emailed == False).order_by(desc(RSSFeedEntry.posted_on_timestamp)).all()
        return unemailed_entries

    def update_feed_last_checked(self, rss_feed: RSSFeed):
        """
        Updates the last checked timestamp for an RSS feed in the database.

        Args:
            rss_feed: An RSSFeed object to be updated.

        Raises:
            SQLAlchemyError: If there is an error updating the feed.
        """
        time_utc = datetime.datetime.utcnow()
        rss_feed.last_checked_timestamp = time_utc
        self._commit()

    def add_feed(self, url: str) -> RSSFeed:
        """
        Adds a new RSS feed to the database.

        Args:
            url: A string representing the URL of the RSS feed.

        Returns:
            The newly created RSSFeed object.

        Raises:
            SQLAlchemyError: If there is an error adding the feed.
        """
        feed = RSSFeed(url=url)
        self._session.add(feed)
        self._commit()
        return feed
