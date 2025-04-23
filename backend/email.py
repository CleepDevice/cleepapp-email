#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
import mimetypes
import os
from email.message import EmailMessage
from cleep.core import CleepRenderer
from cleep.exception import CommandError, MissingParameter
from cleep.profiles.alertprofile import AlertProfile
from cleep.libs.internals.tools import TRACE

__all__ = ["Email"]


class Email(CleepRenderer):
    """
    Email application
    """

    MODULE_AUTHOR = "Cleep"
    MODULE_VERSION = "2.0.0"
    MODULE_PRICE = 0.0
    MODULE_DEPS = []
    MODULE_DESCRIPTION = "Sends you alerts by email."
    MODULE_LONGDESCRIPTION = (
        "This module allows your device to send alert by email and other events "
        "that occured and should be noticed by your device.<br>This module "
        "implements natively connectors to Google Gmail, Yahoo! mail and your own email server."
    )
    MODULE_TAGS = ["email", "smtp", "alert"]
    MODULE_CATEGORY = "SERVICE"
    MODULE_COUNTRY = None
    MODULE_URLINFO = "https://github.com/tangb/cleepmod-email"
    MODULE_URLHELP = "https://github.com/tangb/cleepmod-email/wiki"
    MODULE_URLSITE = None
    MODULE_URLBUGS = "https://github.com/tangb/cleepmod-email/issues"

    MODULE_CONFIG_FILE = "email.conf"
    DEFAULT_CONFIG = {
        "provider": "custom",
        "server": None,
        "port": None,
        "login": None,
        "password": None,
        "tls": False,
        "ssl": False,
        "sender": None,
    }

    RENDERER_PROFILES = [AlertProfile]

    CUSTOM_PROVIDER_KEY = "custom"
    PROVIDERS = {
        "gmail": {
            "label": "Google Gmail",
            "server": "smtp.gmail.com",
            "port": 465,
            "tls": False,
            "ssl": True,
        },
        "yahoo": {
            "label": "Yahoo! Mail",
            "server": "smtp.mail.yahoo.com",
            "port": 587,
            "tls": True,
            "ssl": False,
        },
        "outlook": {
            "label": "Outlook",
            "server": "smtp-mail.outlook.com",
            "port": 587,
            "tls": True,
            "ssl": False,
        },
    }

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled (bool): flag to set debug level to logger
        """
        CleepRenderer.__init__(self, bootstrap, debug_enabled)

    def get_module_config(self):
        """
        Return full module configuration

        Returns:
            dict: configuration::

                {
                    server (str): custom smtp server address
                    port (int): custom smtp server port
                    tls (bool): TLS option
                    ssl (bool): SSL option
                    login (string): smtp server login
                    sender (string): default sender
                    provider (str): configured provider
                    providers (list): list of provider names::

                        (
                            {
                                label (str): provider friendly name
                                key (str): provider key
                            },
                            ...
                        )

                }

        """
        config = self._get_config()

        # append providers
        config["providers"] = []
        for provider_name, provider in Email.PROVIDERS.items():
            config["providers"].append(
                {"label": provider["label"], "key": provider_name}
            )
        config["providers"].append(
            {"label": "Custom email provider", "key": Email.CUSTOM_PROVIDER_KEY}
        )

        # delete configured password
        del config["password"]

        return config

    def test(self, recipient):
        """
        Send email test according to current configuration

        Args:
            recipient (str): coma separated recipients

        Returns:
            bool: True if test email sent successfully
        """
        return self.send_email(
            "Cleep test", "This is a test email from your Cleep device", recipient
        )

    def send_email(
        self,
        subject,
        content,
        recipient,
        cc=None,
        bcc=None,
        attachments=None,
        sender=None,
    ):
        """
        Send test email

        Args:
            subject (str): email subject
            content (str): email content. Html or text. Content will be always embedded in base html tags.
            recipient (str): coma separated recipients
            cc (str, optional): coma separated carbon copy recipients. Defaults to None
            bcc (str, optional): coma separated blind carbon copy recipients. Defaults to None
            attachments (list, optional): list of attachments. Must be filepaths. Defaults to None::

                ( filepath1, filepath2, ...)

            sender (str, optional): overwrite default sender. Defaults to None

        Returns:
            bool: True if message sent successfully. Nonetheless email may returned in error afterwards.
        """
        self._check_parameters(
            [
                {
                    "name": "subject",
                    "value": subject,
                    "type": str,
                    "empty": False,
                    "none": False,
                },
                {
                    "name": "content",
                    "value": content,
                    "type": str,
                    "empty": False,
                    "none": False,
                },
                {
                    "name": "recipient",
                    "value": recipient,
                    "type": str,
                    "empty": False,
                    "none": False,
                },
                {
                    "name": "cc",
                    "value": cc,
                    "type": str,
                    "none": True,
                },
                {
                    "name": "bcc",
                    "value": bcc,
                    "type": str,
                    "none": True,
                },
                {
                    "name": "attachments",
                    "value": attachments,
                    "type": list,
                    "none": True,
                    "validator": lambda val: all(isinstance(v,str) for v in val),
                },
                {
                    "name": "sender",
                    "value": sender,
                    "type": str,
                    "empty": False,
                    "none": True,
                },
            ]
        )

        config = self.__get_config()
        if attachments is None:
            attachments = []

        try:
            mail = EmailMessage()
            mail["Subject"] = subject
            mail["From"] = sender or config.get("sender")
            mail["To"] = recipient
            mail.preamble = "You will not see this in a MIME-aware mail reader.\n"
            mail.add_alternative(f"<html><head></head><body>{content}</body>")

            for attachment in attachments:
                if not os.path.isfile(attachment):
                    continue
                ctype, encoding = mimetypes.guess_type(attachment)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"
                maintype, subtype = ctype.split("/", 1)
                with open(attachment, "rb") as filep:
                    mail.add_attachment(
                        filep.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=os.path.basename(attachment),
                    )

            smtp_server = None
            server = config.get("server")
            port = config.get("port")
            ssl = config.get("ssl", False)
            self.logger.debug("SSL enabled: %s", ssl)
            if ssl:
                self.logger.debug("Connect SMTP server with SSL on %s:%s", server, port)
                smtp_server = smtplib.SMTP_SSL(server, port)
            else:
                self.logger.debug(
                    "Connect SMTP server without SSL on %s:%s", server, port)
                smtp_server = smtplib.SMTP(server, port)
            self.logger.debug("Smtp server: %s", smtp_server)
            if self.logger.getEffectiveLevel() == TRACE:
                smtp_server.set_debuglevel(True)
            if config.get("tls"):
                self.logger.debug("StartTLS session")
                smtp_server.starttls()
            if config.get("login"):
                self.logger.debug("Connect to server using credentials")
                smtp_server.login(config.get("login"), config.get("password"))
            self.logger.debug("Connected to server")

            smtp_server.send_message(mail)
            smtp_server.quit()

            return True

        except smtplib.SMTPServerDisconnected as error:
            self.logger.exception("Failed to send email:")
            raise CommandError("Server disconnected") from error

        except smtplib.SMTPSenderRefused as error:
            self.logger.exception("Failed to send email:")
            raise CommandError("Email sender must be a valid email address") from error

        except smtplib.SMTPRecipientsRefused as error:
            self.logger.exception("Failed to send email:")
            raise CommandError("Some recipients were refused") from error

        except smtplib.SMTPDataError as error:
            self.logger.exception("Failed to send email:")
            raise CommandError("Problem with email content") from error

        except smtplib.SMTPConnectError as error:
            self.logger.exception("Failed to send email:")
            raise CommandError(
                "Unable to establish connection with smtp server. Please check server address"
            ) from error

        except smtplib.SMTPAuthenticationError as error:
            self.logger.exception("Failed to send email:")
            raise CommandError("Authentication failed. Please check credentials.") from error

        except Exception as error:
            self.logger.exception("Failed to send email:")
            raise CommandError("Unable to send email. Please check configuration") from error

    def __get_config(self):
        """
        Check and return valid configuration

        Returns:
            dict: current configuration ready to be used to send mail::

                {
                    server (str): smtp server address
                    port (int): smtp server port
                    ssl (bool): ssl flag
                    tls (bool): tls flag
                    sender (str): custom sender value
                    login (str): login
                    password (str): password
                }

        Raises:
            MissingParameter: if inconsistent configuration value found
        """
        config = self._get_config()

        if config.get("provider") in Email.PROVIDERS and (
            not config.get("login") or not config.get("password")
        ):
            raise MissingParameter(
                "Credentials must be specified with choosen provider"
            )
        if config["provider"] == Email.CUSTOM_PROVIDER_KEY and (
            not config.get("server") or not config.get("port")
        ):
            raise MissingParameter(
                "Server/port address must be configured when using custom provider"
            )

        provider = config.get("provider")
        if provider == Email.CUSTOM_PROVIDER_KEY:
            return {
                "server": config.get("server"),
                "port": config.get("port"),
                "ssl": config.get("ssl"),
                "tls": config.get("tls"),
                "sender": config.get("sender"),
                "login": config.get("login"),
                "password": config.get("password"),
            }

        return {
            "server": Email.PROVIDERS.get(provider).get("server"),
            "port": Email.PROVIDERS.get(provider).get("port"),
            "ssl": Email.PROVIDERS.get(provider).get("ssl"),
            "tls": Email.PROVIDERS.get(provider).get("tls"),
            "sender": config.get("sender"),
            "login": config.get("login"),
            "password": config.get("password"),
        }

    def set_config(
        self,
        provider,
        server=None,
        port=None,
        login=None,
        password=None,
        tls=False,
        ssl=False,
        sender=None,
    ):
        """
        Set configuration

        Args:
            provider (str): choosen provider from list
            server (str, optional): custom smtp server address
            port (int, optional): smtp server port
            login (str, optional): login to connect to custom smtp server
            password (str, optional): password to connect to custom smtp server
            tls (bool, optional): TLS option. Defaults to False
            ssl (bool, optional): SSL option. Defaults to False
            sender (str, optional): email sender

        Returns:
            bool: True if config saved successfully
        """
        self._check_parameters(
            [
                {
                    "name": "provider",
                    "value": provider,
                    "type": str,
                    "validator": lambda val: val in Email.PROVIDERS or val == Email.CUSTOM_PROVIDER_KEY,
                    "message": "Provider must be choosen from list",
                },
                {
                    "name": "server",
                    "value": server,
                    "type": str,
                    "none": True,
                    "empty": False,
                },
                {
                    "name": "port",
                    "value": port,
                    "type": int,
                    "none": True,
                },
                {
                    "name": "login",
                    "value": login,
                    "type": str,
                    "none": True,
                    "empty": True,
                },
                {
                    "name": "password",
                    "value": password,
                    "type": str,
                    "none": True,
                    "empty": True,
                },
                {
                    "name": "tls",
                    "value": tls,
                    "type": bool,
                    "none": False,
                },
                {
                    "name": "ssl",
                    "value": ssl,
                    "type": bool,
                    "none": False,
                },
                {
                    "name": "sender",
                    "value": sender,
                    "type": str,
                    "none": True,
                    "empty": False,
                },
            ]
        )

        return self._update_config(
            {
                "provider": provider,
                "server": server,
                "port": port,
                "login": login,
                "password": password,
                "tls": tls,
                "ssl": ssl,
                "sender": sender,
            }
        )

    def on_render(self, profile_name, profile_values):
        """
        Render profile

        Args:
            profile_name (str): profile name
            profile_values (dict): profile values

        Returns:
            bool: True if post succeed, False otherwise
        """
        if profile_name != "AlertProfile":
            return False

        try:
            params = {
                "subject": profile_values.get("subject"),
                "content": profile_values.get("message"),
                "attachments": profile_values.get("attachment", []),
                "recipient": self._get_config_field("sender"),
            }
            return self.send_email(**params)
        except Exception as error:
            self.logger.warning("Alert through email not sent: %s", str(error))
            return False
