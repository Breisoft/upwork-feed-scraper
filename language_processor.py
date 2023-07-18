from typing import List, Tuple

import datetime
import re
import pytz

from bs4 import BeautifulSoup


def get_hourly_range(summary: str) -> Tuple:
    """
    Extracts the hourly range from the job summary.

    Args:
        summary (str): The job summary in HTML format.

    Returns:
        Tuple: A tuple containing the low and high ends of the hourly range. If not found, returns (None, None).
    """

    match = re.search(r'Hourly Range</b>: ([\$\d\.]+)-([\$\d\.]+)', summary)

    if match:
        hourly_range_low, hourly_range_high = match.groups()
        return hourly_range_low, hourly_range_high

    return None, None


def get_skills(summary: str) -> str:
    """
    Extracts the skills from the job summary.

    Args:
        summary (str): The job summary in HTML format.

    Returns:
        str: A string containing the skills required for the job. If not found, returns None.
    """

    match = re.search(r'<b>Skills<\/b>:(.*?)<br \/>', summary, re.DOTALL)

    if match:
        skills_str = match.group(1)

        skills = [skill.strip() for skill in skills_str.split(',')]

        skills_final = ', '.join(skill for skill in skills)

        return skills_final

    return None


def get_posted_on_timestamp(summary: str) -> datetime.datetime:
    """
    Extracts the posted on timestamp from a given summary.

    Args:
       summary (str): The job summary in HTML format.

    Returns:
        datetime.datetime: The posted on timestamp as a datetime object in UTC timezone.
                           If no match is found, returns None.
    """

    match = re.search(r'<b>Posted On</b>:\s+(.*?)\s+UTC', summary)

    if match:
        date = match.group(1)

        date_obj = datetime.datetime.strptime(date, "%B %d, %Y %H:%M")
        utc_timezone = pytz.timezone('UTC')
        date_utc = utc_timezone.localize(date_obj)

        return date_utc

    return None


def clean_html_text(html_text: str) -> str:
    """
    Cleans HTML text by removing tags and converting it to plain text.

    Args:
        html_text (str): The HTML text to be cleaned.

    Returns:
        str: The cleaned plain text.
    """

    soup = BeautifulSoup(html_text, 'html.parser')
    raw_text = soup.get_text(separator=' ')
    return raw_text


class NaturalLanguageExtractor():
    """
    NaturalLanguageExtractor is a class that provides functionality to perform keyword extraction from a given text
    using the RAKE (Rapid Automatic Keyword Extraction) algorithm. It uses the Brown Corpus from the NLTK library to
    establish a frequency distribution of words, allowing it to return the top 10 least common keywords.

    Attributes:
        _fdist (nltk.FreqDist): A frequency distribution of words in the Brown Corpus
        _rake (rake_nltk.Rake): Instance of the Rake class from the rake_nltk library used for keyword extraction

    Methods:
        _remove_non_letters(word: str) -> str: Removes non-alphabetic characters from the given word and returns it
        extract_keywords(text: str) -> List[str]: Extracts the top 10 least common keywords from the given text
    """

    def __init__(self):
        import nltk
        from rake_nltk import Rake
        from nltk.corpus import brown

        # Get a list of all words in the Brown Corpus
        words = brown.words()

        # Create a frequency distribution of words
        self._fdist = nltk.FreqDist(words)

        self._rake = Rake()

    @staticmethod
    def _remove_non_letters(word: str) -> str:
        """
        Removes non-alphabetic characters and retains only alphabetic characters.

        Args: 
            word (str): The word that potentially contains non-alphabetic characters

        Returns:
            str: The word or string with only alphabetic characters
        """
        return re.sub('[^a-zA-Z]', '', word)
    
    @staticmethod
    def _remove_urls(text: str) -> str:
        """
        Removes URLs from a given string.

        Args: 
            text (str): The string that may contain URLs

        Returns:
            str: The string with URLs removed
        """

        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        no_url_text = url_pattern.sub(r'', text)
        return no_url_text

    def extract_keywords(self, text: str) -> List[str]:
        """ 
        Extracts the top 10 least common keywords from the given text using RAKE.

        Args:
            text (str): The input text from which to extract keywords

        Returns:
            List[str]: A list of the top 10 keywords
        """

        # Remove URLs from the text so they don't interfere with keyword extraction
        text = NaturalLanguageExtractor._remove_urls(text)

        # Extraction given the text.
        self._rake.extract_keywords_from_text(text)

        # To get keyword phrases ranked highest to lowest.
        key_phrases = self._rake.get_ranked_phrases()

        all_words = set()

        for phrase in key_phrases:
            words = phrase.split(' ')

            # We're not looking for key phrases, we're looking specifically 
            # for technical keywords
            if len(words) != 1:
                continue

            word = words[0]

            cleaned_word = NaturalLanguageExtractor._remove_non_letters(word)

            if len(cleaned_word) < 1:
                continue

            all_words.add(cleaned_word)

        # Get frequencies for each word
        word_freqs = [(word, self._fdist[word]) for word in all_words]

        keywords = set()

        for word, freq in word_freqs:

            # If frequency < 20, usually this is a rare term in the brown corpus
            # and has a higher probability of being a technical term
            if freq < 20:
                keywords.add((word, freq))

        sorted_keywords = sorted(keywords, key=lambda x: x[1])

        keywords_list = [keyword for keyword, _ in sorted_keywords]

        # Get only the top 10 least common keywords
        return keywords_list[:10]
