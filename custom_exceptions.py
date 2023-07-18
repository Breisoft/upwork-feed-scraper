class MissingCredentialsException(Exception):
    """
    Custom exception class to indicate that some required credentials are missing.
    
    Raises:
        Exception: Indicates that the necessary credentials for 
          a certain operation were not provided.
    """

class RSSFeedException(Exception):
    """
    Custom exception class to represent issues related to RSS Feed processing.
    
    Raises:
        Exception: Indicates a failure in RSS Feed processing such as
          fetching entries or invalid feed.
    """

class InvalidSMTPLoginException(Exception):
    """
    Custom exception class to represent issues with SMTP server login during email handling.
    
    Raises:
        Exception: Indicates an issue with logging into the SMTP server,
          such as authentication errors.
    """

class InvalidSMTPAddressException(Exception):
    """
    Custom exception class to handle issues with sender or recipient 
      email addresses during email handling.
    
    Raises:
        Exception: Indicates an issue with the sender or recipient email addresses.
    """
