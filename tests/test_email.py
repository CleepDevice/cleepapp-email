from cleep.libs.tests import session
import unittest
import logging
import sys
sys.path.append('../')
from backend.email import Email
import os
import time
from copy import deepcopy
from unittest.mock import Mock, patch, mock_open
from cleep.libs.tests.common import get_log_level
from cleep.exception import CommandError, MissingParameter, InvalidParameter
import smtplib
from cleep.libs.internals.tools import TRACE

LOG_LEVEL = get_log_level()

CONFIG_CUSTOM = {
    "server": "server",
    "port": 123,
    "tls": True,
    "ssl": False,
    "login": "my-login",
    "password": "my-password",
    "provider": "custom"
}

class TestEmail(unittest.TestCase):

    def setUp(self):
        self.session = session.TestSession(self)
        logging.basicConfig(level=LOG_LEVEL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        self.app = self.session.setup(Email)

    def tearDown(self):
        self.session.clean()

    def test_get_module_config(self):
        self.app._get_config = Mock(return_value=deepcopy(CONFIG_CUSTOM))

        result = self.app.get_module_config()
        logging.debug('Result: %s', result)

        self.assertEqual(result, {
            "server": "server",
            "port": 123,
            "tls": True,
            "ssl": False,
            "login": "my-login",
            "provider": "custom",
            "providers": [
                {"key": "gmail", "label": "Google Gmail"},
                {"key": "yahoo", "label": "Yahoo! Mail"},
                {"key": "custom", "label": "Custom email provider"},
            ],
        })

    def test_test(self):
        recipient = "cleep@yopmail.com"
        self.app.send_email = Mock(return_value=True)

        result = self.app.test(recipient)

        self.assertTrue(result)
        self.app.send_email.assert_called_with("Cleep test", "This is a test email from your Cleep device", recipient)

    def test_test_failure(self):
        recipient = "cleep@yopmail.com"
        self.app.send_email = Mock(return_value=False)

        result = self.app.test(recipient)

        self.assertFalse(result)

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    @patch("backend.email.os.path.isfile", Mock(return_value=True))
    @patch("backend.email.mimetypes.guess_type", Mock(return_value=(None, None)))
    @patch("backend.email.open", new_callable=mock_open, read_data="some content")
    def test_send_email_ssl(self, open_mock, smtpssl_mock, emailmessage_mock):
        self.app._Email__get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
            "ssl": True,
        })

        self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc', ['/tmp/attachment1.txt'], 'forced-sender')

        emailmessage_mock.return_value.__setitem__.assert_any_call('To', 'recipient')
        emailmessage_mock.return_value.__setitem__.assert_any_call('Subject', 'test')
        emailmessage_mock.return_value.__setitem__.assert_any_call('From', 'forced-sender')
        emailmessage_mock.return_value.add_attachment.assert_called_with("some content", maintype="application", subtype="octet-stream", filename="attachment1.txt")
        smtpssl_mock.return_value.send_message.assert_called()

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP")
    @patch("backend.email.os.path.isfile", Mock(return_value=True))
    @patch("backend.email.mimetypes.guess_type", Mock(return_value=(None, None)))
    @patch("backend.email.open", new_callable=mock_open, read_data="some content")
    def test_send_email(self, open_mock, smtp_mock, emailmessage_mock):
        self.app._Email__get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
            "ssl": False,
        })

        self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc', ['/tmp/attachment1.txt'], 'forced-sender')

        emailmessage_mock.return_value.__setitem__.assert_any_call('To', 'recipient')
        emailmessage_mock.return_value.__setitem__.assert_any_call('Subject', 'test')
        emailmessage_mock.return_value.__setitem__.assert_any_call('From', 'forced-sender')
        emailmessage_mock.return_value.add_attachment.assert_called_with("some content", maintype="application", subtype="octet-stream", filename="attachment1.txt")
        smtp_mock.return_value.send_message.assert_called()

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP")
    @patch("backend.email.os.path.isfile", Mock(return_value=True))
    @patch("backend.email.mimetypes.guess_type", Mock(return_value=(None, None)))
    @patch("backend.email.open", new_callable=mock_open, read_data="some content")
    def test_send_email_tls(self, open_mock, smtp_mock, emailmessage_mock):
        self.app._Email__get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
            "tls": True,
        })

        self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc', ['/tmp/attachment1.txt'], 'forced-sender')

        smtp_mock.return_value.starttls.assert_called()

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP")
    @patch("backend.email.os.path.isfile", Mock(return_value=True))
    @patch("backend.email.mimetypes.guess_type", Mock(return_value=(None, None)))
    @patch("backend.email.open", new_callable=mock_open, read_data="some content")
    def test_send_email_enable_debug(self, open_mock, smtp_mock, emailmessage_mock):
        self.app._Email__get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
            "tls": True,
        })
        orig_getEffectiveLevel = self.app.logger.getEffectiveLevel
        self.app.logger.getEffectiveLevel = Mock(side_effect=[TRACE])

        self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc', ['/tmp/attachment1.txt'], 'forced-sender')

        smtp_mock.return_value.set_debuglevel.assert_called()
        self.app.logger.getEffectiveLevel = orig_getEffectiveLevel

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    @patch("backend.email.os.path.isfile", Mock(return_value=False))
    @patch("backend.email.mimetypes.guess_type", Mock(return_value=(None, None)))
    @patch("backend.email.open", new_callable=mock_open, read_data="some content")
    def test_send_email_invalid_attachment_path(self, open_mock, smtpssl_mock, emailmessage_mock):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })
        
        self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc', ['/tmp/attachment1.txt'], 'forced-sender')

        open_mock.assert_not_called()
        emailmessage_mock.return_value.add_attachment.assert_not_called()

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    def test_send_email_smtp_server_disconnected(self, smtpssl_mock, emailmessage_mock):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })
        smtpssl_mock.return_value.send_message.side_effect = smtplib.SMTPServerDisconnected()
        
        with self.assertRaises(CommandError) as cm:
            self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc')
        self.assertEqual(str(cm.exception), 'Server disconnected')

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    def test_send_email_smtp_sender_refused(self, smtpssl_mock, emailmessage_mock):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })
        smtpssl_mock.return_value.send_message.side_effect = smtplib.SMTPSenderRefused(code=123, msg="message", sender="email")
        
        with self.assertRaises(CommandError) as cm:
            self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc')
        self.assertEqual(str(cm.exception), 'Email sender must be a valid email address')

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    def test_send_email_smtp_recipients_refused(self, smtpssl_mock, emailmessage_mock):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })
        smtpssl_mock.return_value.send_message.side_effect = smtplib.SMTPRecipientsRefused(recipients="recipients")
        
        with self.assertRaises(CommandError) as cm:
            self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc')
        self.assertEqual(str(cm.exception), "Some recipients were refused")
        
    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    def test_send_email_smtp_data_error(self, smtpssl_mock, emailmessage_mock):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })
        smtpssl_mock.return_value.send_message.side_effect = smtplib.SMTPDataError(code=123, msg="error")
        
        with self.assertRaises(CommandError) as cm:
            self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc')
        self.assertEqual(str(cm.exception), "Problem with email content")

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    def test_send_email_smtp_connect_error(self, smtpssl_mock, emailmessage_mock):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })
        smtpssl_mock.return_value.send_message.side_effect = smtplib.SMTPConnectError(code=123, msg="error")
        
        with self.assertRaises(CommandError) as cm:
            self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc')
        self.assertEqual(str(cm.exception), "Unable to establish connection with smtp server. Please check server address")

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    def test_send_email_smtp_authentication_error(self, smtpssl_mock, emailmessage_mock):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })
        smtpssl_mock.return_value.send_message.side_effect = smtplib.SMTPAuthenticationError(code=123, msg="error")
        
        with self.assertRaises(CommandError) as cm:
            self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc')
        self.assertEqual(str(cm.exception), "Authentication failed. Please check credentials.")

    @patch("backend.email.EmailMessage")
    @patch("backend.email.smtplib.SMTP_SSL")
    def test_send_email_non_smtp_error(self, smtpssl_mock, emailmessage_mock):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })
        smtpssl_mock.return_value.send_message.side_effect = Exception("Test error")
        
        with self.assertRaises(CommandError) as cm:
            self.app.send_email('test', 'some email content', 'recipient', 'cc', 'bcc')
        self.assertEqual(str(cm.exception), "Unable to send email. Please check configuration")

    def test__get_config_for_known_provider(self):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "password": "password",
        })

        config = self.app._Email__get_config()
        logging.debug("Config: %s", config)

        self.assertDictEqual(config, {
            "server": "smtp.gmail.com",
            "port": 465,
            "ssl": True,
            "tls": False,
            "sender": None,
            "login": "login",
            "password": "password",
        })

    def test__get_config_for_custom_provider(self):
        self.app._get_config = Mock(return_value={
            "server": "server.com",
            "port": 123,
            "provider": "custom",
            "login": "login",
            "password": "password",
            "tls": True,
            "ssl": True,
            "sender": "someone@test.com"
        })

        config = self.app._Email__get_config()
        logging.debug("Config: %s", config)

        self.assertDictEqual(config, {
            "server": "server.com",
            "port": 123,
            "ssl": True,
            "tls": True,
            "sender": "someone@test.com",
            "login": "login",
            "password": "password",
        })

    def test__get_config_no_login_for_known_provider(self):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "password": "password",
            "tls": True,
            "ssl": True,
            "sender": "someone@test.com"
        })

        with self.assertRaises(MissingParameter) as cm:
            config = self.app._Email__get_config()
            logging.debug("Config: %s", config)
        self.assertEqual(str(cm.exception), "Credentials must be specified with choosen provider")

    def test__get_config_no_password_for_known_provider(self):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "logind",
            "tls": True,
            "ssl": True,
            "sender": "someone@test.com"
        })

        with self.assertRaises(MissingParameter) as cm:
            config = self.app._Email__get_config()
            logging.debug("Config: %s", config)
        self.assertEqual(str(cm.exception), "Credentials must be specified with choosen provider")

    def test__get_config_no_password_for_known_provider(self):
        self.app._get_config = Mock(return_value={
            "provider": "gmail",
            "login": "login",
            "tls": True,
            "ssl": True,
            "sender": "someone@test.com"
        })

        with self.assertRaises(MissingParameter) as cm:
            config = self.app._Email__get_config()
            logging.debug("Config: %s", config)
        self.assertEqual(str(cm.exception), "Credentials must be specified with choosen provider")

    def test__get_config_no_server_for_custom_provider(self):
        self.app._get_config = Mock(return_value={
            "provider": "custom",
            "port": 123,
            "tls": True,
            "ssl": True,
            "sender": "someone@test.com"
        })

        with self.assertRaises(MissingParameter) as cm:
            config = self.app._Email__get_config()
            logging.debug("Config: %s", config)
        self.assertEqual(str(cm.exception), "Server/port address must be configured when using custom provider")

    def test__get_config_no_port_for_custom_provider(self):
        self.app._get_config = Mock(return_value={
            "provider": "custom",
            "server": "server.com",
            "tls": True,
            "ssl": True,
            "sender": "someone@test.com"
        })

        with self.assertRaises(MissingParameter) as cm:
            config = self.app._Email__get_config()
            logging.debug("Config: %s", config)
        self.assertEqual(str(cm.exception), "Server/port address must be configured when using custom provider")

    def test_set_config(self):
        self.app._update_config = Mock(return_value=True)

        saved = self.app.set_config(provider="gmail", login="login", password="password", tls=True, ssl=False)

        self.assertTrue(saved)
        self.app._update_config.assert_called_with({
            "provider": "gmail",
            "login": "login",
            "password": "password",
            "tls": True,
            "ssl": False,
            "server": None,
            "port": None,
            "sender": None,
        })

    def test_set_config_check_params(self):
        with self.assertRaises(InvalidParameter) as cm:
            saved = self.app.set_config(provider="test")
        self.assertEqual(str(cm.exception), "Provider must be choosen from list")

        with self.assertRaises(InvalidParameter) as cm:
            saved = self.app.set_config(provider="custom", server="")
        self.assertEqual(str(cm.exception), 'Parameter "server" is invalid (specified="")')

        # skipped : issue in core fixed in next version
        # with self.assertRaises(InvalidParameter) as cm:
        #     saved = self.app.set_config(provider="custom", port="123")
        # self.assertEqual(str(cm.exception), 'Parameter "port" must be of type "int"')

        # skipped : issue in core fixed in next version
        # with self.assertRaises(InvalidParameter) as cm:
        #     saved = self.app.set_config(provider="gmail", sender="")
        # self.assertEqual(str(cm.exception), 'Parameter "sender" is invalid (specified="")')

    def test_on_render(self):
        values = {
            "subject": "subject",
            "message": "content",
            "attachment": ["attach1.png"],
        }
        self.app._get_config_field = Mock(return_value="sender@email.com")
        self.app.send_email = Mock(return_value=True)

        rendered = self.app.on_render("AlertProfile", values)

        self.assertTrue(rendered)
        self.app.send_email.assert_called_with(subject="subject", content="content", attachments=["attach1.png"], recipient="sender@email.com")

    def test_on_render_send_email_error(self):
        values = {
            "subject": "subject",
            "message": "content",
            "attachment": ["attach1.png"],
        }
        self.app._get_config_field = Mock(return_value="sender@email.com")
        self.app.send_email = Mock(side_effect=Exception("Test error"))

        rendered = self.app.on_render("AlertProfile", values)

        self.assertFalse(rendered)

    def test_on_render_invalid_profile(self):
        self.app.send_email = Mock()

        rendered = self.app.on_render("UnhandledProfile", {})

        self.assertFalse(rendered)
        self.app.send_email.assert_not_called()


if __name__ == "__main__":
    # coverage run --include="**/backend/**/*.py" --concurrency=thread test_email.py; coverage report -m -i
    unittest.main()
    
