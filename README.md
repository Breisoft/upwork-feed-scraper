# Upwork Feed Scraper: Advanced Job Feed Parsing Solution

This repository houses an advanced, Python-oriented RSS feed parser, dedicated to Upwork job feeds. The solution is architected utilizing SQLAlchemy for Object-Relational Mapping (ORM), and it is equipped with custom-defined exceptions to handle varying situations seamlessly.

## Core Capabilities

- **RSS Feed Scraping:** Scraps RSS feeds from Upwork, transposing the entries into a SQL database efficiently and effectively.
- **Keyword Extraction:** An optional feature that intelligently extracts keywords from feed entries to aid in data analysis.
- **Automated Email Updates:** Sends email alerts about newly detected feed entries, ensuring that you always stay on top of the latest job postings.
- **Custom Exception Handling:** Manages unexpected scenarios through a series of custom exceptions, each tailored with its unique error message.

## Core Components

- **RSSFeedEntry:** Depicts an RSS feed entry via a SQL Alchemy ORM class, creating an intuitive way of interacting with each entry.
- **FeedManager:** Orchestrates the entire feed scraping process, encompassing database interactions, email updates, and keyword extraction.
- **Custom Exceptions:** Designed to ensure reliability and easier debugging, including `MissingCredentialsException`, `RSSFeedException`, `InvalidSMTPLoginException`, `InvalidSMTPAddressException`.

## Usage Guidelines

To utilize this advanced scraper, you are required to provide the database details, the target email address for updates, and optionally, the decision to extract keywords from feed entries along with the time interval between each feed check.

## Contributing

We highly appreciate your contributions! Feel free to submit pull requests. If you're considering a significant alteration, please open an issue first for discussion.

## Licensing

This project is licensed under the terms of the MIT License.
