from typing import List, Tuple, Optional
from datetime import timedelta

import os
import time
import logging
import datetime
import asyncio
import aiohttp
import feedparser

from custom_exceptions import RSSFeedException

from database import Database, RSSFeed, RSSFeedEntry

from email_renderer import render_html
from email_handler import EmailAccount, Email

from language_processor import NaturalLanguageExtractor, get_posted_on_timestamp
from language_processor import get_skills, get_hourly_range, clean_html_text


class FeedManager():
    """
    Manages the fetching, processing, and storage of RSS feeds. 

    This class is responsible for maintaining a list of RSS feeds and processing new entries. 
    It also handles emailing updates about new entries, and can optionally extract keywords from each entry.

    Args:
        db (Database): The database to use.
        to_address (str): The email address to send updates to.
        extract_keywords (Optional[bool]): Whether to extract keywords from feed entries. Defaults to False.
        wait_seconds (Optional[int]): The time to wait between each feed check. Defaults to 60 seconds.

    Attributes:
        _db (Database): The database to use.
        _to_address (str): The email address to send updates to.
        _extract_keywords (bool): Whether to extract keywords from feed entries.
        _wait_seconds (int): The time to wait between each feed check.
        _feeds (list): The list of all RSS feeds.
        _existing_feed_urls (set): The set of all URLs from previously processed feed entries.
        _nlp (NaturalLanguageExtractor): A natural language processing utility for keyword extraction.
        _email_account (EmailAccount): An email account used to send email updates.
    """

    def __init__(self, db: Database, to_address: str,
                 extract_keywords: Optional[bool] = False,
                 wait_seconds: Optional[int] = 60):
        """
        Initialize a FeedManager.

        Args:
            db (Database): The database to use.
            to_address (str): The email address to send updates to.
            extract_keywords (Optional[bool]): Whether to extract keywords from feed entries. Defaults to False.
            wait_seconds (Optional[int]): The time to wait between each feed check. Defaults to 60 seconds.
        """

        self._db = db
        self._to_address = to_address

        self._extract_keywords = extract_keywords
        self._wait_seconds = wait_seconds

        self._feeds = []

        self._existing_feed_urls = set()

        if self._extract_keywords:
            self._nlp = NaturalLanguageExtractor()

        self._email_account = EmailAccount()

    def _load_existing_feeds(self):

        # Load all feeds from the database
        feeds = self._db.get_all_feeds()

        # Load all feed entries from the database
        feed_entries = self._db.get_all_feed_entries()

        # Mark each of the feed entries urls as already scraped so we don't do duplicates
        for feed_entry in feed_entries:
            self._existing_feed_urls.add(feed_entry.url)

        self._feeds = feeds

    async def add_new_feed(self, url: str):
        """
        Add a new RSS feed to the application and database.

        Args:
            url (str): the URL of the RSS feed to be added.

        Raises:
            RSSFeedException: If the URL is invalid, and HTTP error is encountered,
             or if the feed contains zero entries
        """

        entries = await self._get_entries(url, first_fetch=True)

        # Add the RSS feed to the database
        rss_feed = self._db.add_feed(url)

        # Append the RSS feed to the list of feeds
        self._feeds.append(rss_feed)

        # Process the fetched entries
        self._process_entries(rss_feed, entries)

    async def _get_entries(self, url: str, first_fetch: Optional[bool] = False) -> list:

        # Fetch HTTP response from the RSS feed
        response_text = await self._fetch_entries_http(url)

        if not response_text and first_fetch:
            raise RSSFeedException(
                f'Failed to fetch entries from {url} or no entries found.')

        parsed_feed = feedparser.parse(response_text)

        entries = parsed_feed.entries

        if len(entries) < 1 and first_fetch:
            raise RSSFeedException(
                f'No entries found from {url}')

        return entries

    def _process_entries(self, source: RSSFeed, entries: list):

        if entries is None:
            return

        processed_entries = []

        for entry in entries:
            processed_entry = self._process_single_entry(entry, source)
            if processed_entry is not None:
                processed_entries.append(processed_entry)

        self._add_entries_to_db_and_existing_urls(processed_entries)

    def _extract_and_clean_data(self, entry: dict) -> Tuple[str, str]:
        title = entry['title']

        # Remove the '- Upwork' string that's in the RSS Entry title
        if '- Upwork' in title:
            title = title.replace('- Upwork', '').strip()

        title = clean_html_text(title)

        html_summary = entry['summary']
        summary = clean_html_text(html_summary)

        return title, html_summary, summary

    def _add_entries_to_db_and_existing_urls(self, processed_entries: list):
        if len(processed_entries) > 0:
            self._db.insert_entries(processed_entries)

        for processed_entry in processed_entries:
            self._existing_feed_urls.add(processed_entry.url)

    def _process_single_entry(self, entry: dict, source: RSSFeed) -> Optional[RSSFeedEntry]:
        url = entry['link']

        # If we already scraped this url, skip it
        if url in self._existing_feed_urls:
            return None

        title, html_summary, summary = self._extract_and_clean_data(entry)

        posted_on_timestamp = get_posted_on_timestamp(html_summary)
        low_hourly, high_hourly = get_hourly_range(html_summary)
        skills = get_skills(html_summary)

        if self._extract_keywords:
            keywords_ls = self._nlp.extract_keywords(summary)
            keywords = ', '.join(keyword for keyword in keywords_ls)
        else:
            keywords = ''

        processed_entry = RSSFeedEntry(url=url, rss_feed=source,
                                       posted_on_timestamp=posted_on_timestamp,
                                       low_hourly=low_hourly, high_hourly=high_hourly,
                                       skills=skills, title=title, keywords=keywords)
        return processed_entry

    def _get_time_ago_string(self, date_utc: datetime.datetime) -> str:
        # Get the current UTC time
        current_utc = datetime.datetime.utcnow()

        # Calculate the time difference
        time_diff = current_utc - date_utc

        # Convert time difference to minutes, hours, or days
        if time_diff < timedelta(minutes=1):
            time_ago = "just now"
        elif time_diff < timedelta(hours=1):
            minutes = int(time_diff.total_seconds() / 60)
            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif time_diff < timedelta(days=1):
            hours = int(time_diff.total_seconds() / 3600)
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = time_diff.days
            time_ago = f"{days} day{'s' if days > 1 else ''} ago"

        return time_ago

    def _send_email(self, processed_entries: List[RSSFeedEntry]):

        if len(processed_entries) < 1:
            return

        # Adds a new 'time ago' attribute for HTML rendering
        for processed_entry in processed_entries:
            processed_entry.time_ago = self._get_time_ago_string(
                processed_entry.posted_on_timestamp)

        email_content = render_html(processed_entries)

        entry_count = len(processed_entries)

        email = Email(self._email_account, self._to_address,
                      f'Upwork RSS Feed Update ({entry_count})', email_content)

        email.send()

        self._db.update_entries_emailed(processed_entries)

    async def _fetch_entries_http(self, feed_url: str) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(feed_url) as response:
                    response.raise_for_status()
                    return await response.text()

            except aiohttp.ClientConnectionError as exc:
                logging.error("Connection error to %s: %s", feed_url, exc)
                return None
            except aiohttp.ClientPayloadError as exc:
                logging.error("Payload error from %s: %s", feed_url, exc)
                return None
            except aiohttp.ClientResponseError as exc:
                logging.error("Response error from %s: %s", feed_url, exc)
                return None
            except aiohttp.ClientError as exc:
                logging.error(
                    "General client error fetching feed from %s: %s", feed_url, exc)
                return None
            except asyncio.TimeoutError as exc:
                logging.error(
                    "Timeout error fetching feed from %s: %s", feed_url, exc)
                return None

    async def _get_and_process_feed(self, rss_feed: RSSFeed):
        entries = await self._get_entries(rss_feed.url)

        self._process_entries(rss_feed, entries)

        self._db.update_feed_last_checked(rss_feed)

    async def run_feed_loop(self):
        """
        Continuously loops over all available RSS feeds, fetches and processes their entries.
        This method also sends an email with entries that haven't been emailed yet.
        It waits a certain amount of time between each loop iteration, ensuring that
        each feed is only checked after a specific interval.
        """

        while True:
            # Go through all feeds, fetch and process the entries

            ready_feeds = []
            now_utc = datetime.datetime.utcnow()

            max_wait_time = 0

            for rss_feed in self._feeds:

                delta = (now_utc - rss_feed.last_checked_timestamp).total_seconds()

                if delta >= self._wait_seconds:
                    ready_feeds.append(rss_feed)
                else:
                    wait_time = self._wait_seconds - delta

                    if wait_time > max_wait_time:
                        max_wait_time = wait_time

            # Use aiohttp to asynchronously fetch RSS feeds
            await asyncio.gather(*[
                self._get_and_process_feed(rss_feed) for rss_feed in ready_feeds])

            # Get unemailed entries from the database
            unemailed_entries = self._db.get_unemailed_entries()

            # Send email with unemailed entries
            self._send_email(unemailed_entries)

            await asyncio.sleep(max_wait_time)
