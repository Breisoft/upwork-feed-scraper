import unittest
from unittest.mock import MagicMock, patch

from email_handler import EmailAccount, Email, validate_email
from custom_exceptions import MissingCredentialsException, InvalidSMTPLoginException
from custom_exceptions import InvalidSMTPAddressException


class TestValidateEmail(unittest.TestCase):

    def test_valid_email(self):
        valid_email = "john.doe@example.com"
        self.assertTrue(validate_email(valid_email))

    def test_invalid_email(self):
        invalid_email = "john.doe@123"
        self.assertFalse(validate_email(invalid_email))


class TestEmailAccount(unittest.TestCase):

    @patch.dict('os.environ', {
        'EMAIL_SERVER': 'smtp.gmail.com',
        'EMAIL_PORT': '587',
        'EMAIL_USERNAME': 'john.doe@example.com',
        'EMAIL_PASSWORD': 'password123'
    })
    def test_init(self):
        email_account = EmailAccount()

        self.assertEqual(email_account.server, 'smtp.gmail.com')
        self.assertEqual(email_account.port, '587')
        self.assertEqual(email_account.from_address, 'john.doe@example.com')
        self.assertEqual(email_account.password, 'password123')

    @patch.dict('os.environ', {}, clear=True)
    def test_missing_credentials(self):
        with self.assertRaises(MissingCredentialsException):
            EmailAccount()

    @patch.dict('os.environ', {
        'EMAIL_SERVER': 'smtp.gmail.com',
        'EMAIL_PORT': '587',
        'EMAIL_USERNAME': 'john.doe@123',
        'EMAIL_PASSWORD': 'password123'
    })
    def test_invalid_from_address(self):
        with self.assertRaises(InvalidSMTPAddressException):
            EmailAccount()


class TestEmail(unittest.TestCase):

    def setUp(self):
        self.email_account = MagicMock(spec=EmailAccount)
        self.email_account.server = "smtp.gmail.com"
        self.email_account.port = "587"
        self.email_account.from_address = "john.doe@example.com"
        self.email_account.password = "password123"
        self.to_address = "jane.doe@example.com"
        self.subject = "Test Subject"
        self.body = "<p>Hello, World!</p>"

    def test_init(self):
        email = Email(self.email_account, self.to_address, self.subject, self.body)

        self.assertEqual(email._email_account, self.email_account)
        self.assertEqual(email._to_address, self.to_address)
        self.assertEqual(email._subject, self.subject)
        self.assertEqual(email._body, self.body)

    def test_invalid_to_address(self):
        with self.assertRaises(InvalidSMTPAddressException):
            Email(self.email_account, "jane.doe@123", self.subject, self.body)

    @patch('smtplib.SMTP')
    def test_send(self, mock_smtp):
        email = Email(self.email_account, self.to_address, self.subject, self.body)

        mock_smtp_instance = mock_smtp.return_value.__enter__.return_value

        email.send()

        mock_smtp.assert_called_once_with(self.email_account.server, self.email_account.port)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with(
            self.email_account.from_address, self.email_account.password)
        mock_smtp_instance.send_message.assert_called_once()



if __name__ == '__main__':
    unittest.main()
