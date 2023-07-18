import smtplib
import logging
import os
import traceback
import re

from smtplib import SMTPConnectError, SMTPNotSupportedError, SMTPAuthenticationError
from smtplib import SMTPSenderRefused, SMTPRecipientsRefused, SMTPServerDisconnected

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from custom_exceptions import MissingCredentialsException, InvalidSMTPLoginException
from custom_exceptions import InvalidSMTPAddressException


def validate_email(email: str):
    """
    Validates if a given string is a valid email address.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email address is valid, False otherwise.
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


class EmailAccount():
    """
    Represents an Email Account. The credentials for the email account are 
    read from environment variables.
    """

    def __init__(self):
        """
        Initialize the EmailAccount instance by reading the email credentials.
        """

        self._read_credentials()

    def _read_credentials(self):
        """
        Reads the email credentials from environment variables. Raises exceptions if 
        the credentials are not found or the email address is invalid.

        Raises:
            MissingCredentialsException: 
                If the credentials cannot be found in the environment variables.

            InvalidSMTPAddressException: If the from_address email is not valid.
        """

        try:
            self.server = os.environ['EMAIL_SERVER']
            self.port = os.environ['EMAIL_PORT']
            self.from_address = os.environ['EMAIL_USERNAME']
            self.password = os.environ['EMAIL_PASSWORD']
        except KeyError as exc:
            raise MissingCredentialsException(
                'Could not find email credentials from .env file!') from exc

        valid_email = validate_email(self.from_address)

        if valid_email is False:
            raise InvalidSMTPAddressException(
                'from_address is not a valid email address!')


class Email():
    """
    Represents an Email that can be sent using an EmailAccount.
    """

    def __init__(self, email_account: str, to_address: str, subject: str, body: str):
        """
        Initialize the Email instance.

        Args:
            email_account (str): The EmailAccount instance to use to send the email.
            to_address (str): The email address to send the email to.
            subject (str): The subject of the email.
            body (str): The body of the email.

        Raises:
            InvalidSMTPAddressException: If the to_address email is not valid.
        """

        self._email_account = email_account
        self._to_address = to_address
        self._subject = subject
        self._body = body

        valid_email = validate_email(self._to_address)

        if valid_email is False:
            raise InvalidSMTPAddressException(
                'to_address is not a valid email address!')

    def send(self):
        """
        Sends the email using the given EmailAccount. Exceptions are raised if there
        are issues connecting to the SMTP server or sending the email.

        Raises:
            InvalidSMTPLoginException: If there are issues authenticating with the SMTP server.
            InvalidSMTPAddressException: If there are issues with the sender or recipient addresses.
        """

        # Create a multipart message
        msg = MIMEMultipart()
        msg['From'] = self._email_account.from_address
        msg['To'] = self._to_address
        msg['Subject'] = self._subject

        # Attach the message to the email
        msg.attach(MIMEText(self._body, 'html'))

        try:
            # Establish a connection to the SMTP server
            with smtplib.SMTP(self._email_account.server, self._email_account.port) as server:
                # Start TLS encryption
                server.starttls()

                # Login to the email account
                server.login(self._email_account.from_address,
                             self._email_account.password)

                # Send the email
                server.send_message(msg)
        except (SMTPNotSupportedError, SMTPAuthenticationError) as exc:
            raise InvalidSMTPLoginException(
                'Unable to connect/authenticate to SMTP server') from exc
        except (SMTPSenderRefused, SMTPRecipientsRefused) as exc:
            raise InvalidSMTPAddressException(
                'Invalid sender or receipent address') from exc
        except (SMTPConnectError, SMTPServerDisconnected) as exc:
            logging.error("Failed to connect or lost connection: %s", exc)
        except Exception as exc:
            logging.error(
                "Unknown error occurred while sending email: %s", exc, exc_info=True)
            raise
