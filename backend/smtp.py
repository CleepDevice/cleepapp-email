#!/usr/bin/env python
# -*- coding: utf-8 -*-
    
import logging
from raspiot.raspiot import RaspIotRenderer
from raspiot.utils import CommandError, MissingParameter
from raspiot.events.alertEmailProfile import AlertEmailProfile
import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

__all__ = [u'Smtp']


class Smtp(RaspIotRenderer):
    """
    Smtp module
    """
    MODULE_AUTHOR = u'Cleep'
    MODULE_VERSION = u'1.0.0'
    MODULE_PRICE = 0
    MODULE_DEPS = []
    MODULE_DESCRIPTION = u'Sends you alerts by email.'
    MODULE_LONGDESCRIPTION = u'This module allows your device to send alert by email and other events that occured and should be noticed by your device.<br>This module implements natively connectors to Google Gmail, Yahoo! mail and your own email server.'
    MODULE_TAGS = [u'email', u'smtp', u'alert']
    MODULE_CATEGORY = u'SERVICE'
    MODULE_COUNTRY = None
    MODULE_URLINFO = u'https://github.com/tangb/cleepmod-smtp'
    MODULE_URLHELP = u'https://github.com/tangb/cleepmod-smtp/wiki'
    MODULE_URLSITE = None
    MODULE_URLBUGS = u'https://github.com/tangb/cleepmod-smtp/issues'

    MODULE_CONFIG_FILE = u'smtp.conf'
    DEFAULT_CONFIG = {
        u'provider': 'custom',
        u'server': None,
        u'port': None,
        u'login': None,
        u'password': None,
        u'tls': False,
        u'ssl': False,
        u'sender': None
    }

    RENDERER_PROFILES = [AlertEmailProfile]
    RENDERER_TYPE = u'alert.email'

    PROVIDERS = {
        u'gmail': {
            u'label': 'Google Gmail',
            u'server': u'smtp.gmail.com',
            u'port': 465,
            u'tls': False,
            u'ssl': True
        },
        u'yahoo': {
            u'label': 'Yahoo! Mail',
            u'server': u'smtp.mail.yahoo.com',
            u'port': 587,
            u'tls': True,
            u'ssl': False
        }
    }

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled (bool): flag to set debug level to logger
        """
        #init
        RaspIotRenderer.__init__(self, bootstrap, debug_enabled)

    def get_module_config(self):
        """
        Return full module configuration

        Returns:
            dict: configuration::
                {
                    server: server address
                    port: server port
                    tls: TLS option
                    ssl: SSL option
                    login: server login
                    sender: sender email address
                    provider: configured provider
                    providers: list of provider names
                }
        """
        config = self._get_config()
        config[u'providers'] = []
        for provider in self.PROVIDERS:
            config[u'providers'].append({
                u'label': self.PROVIDERS[provider][u'label'],
                u'key': provider
            })
        config[u'providers'].append({
            u'label': u'Custom email provider',
            u'key': u'custom'
        })
        del config[u'password']

        return config

    def __send_email(self, server, port, login, password, tls, ssl, sender, data):
        """
        Send test email

        Params:
            server (string): smtp server address
            port (int): smtp server port
            login (string): login to connect to smtp server
            password (string): password to connect to smtp server
            tls (bool): TLS option
            ssl (bool): SSL option
            sender (string): email sender
            data (AlertEmailProfile): email data

        Returns:
            bool: True if test succeed
        """
        try:
            #make sure port is valid
            if port is not None and (isinstance(port, str) or isinstance(port, unicode)) and len(port)==0:
                port = None
            elif not isinstance(port, int):
                port = int(port)

            #prepare email
            mail = MIMEMultipart(u'related')
            mail[u'Subject'] = data.subject
            mail[u'From'] = sender
            mail[u'To'] = data.recipients[0]
            content = MIMEMultipart(u'alternative')
            mail.attach(content)
            text = u"""%s""" % (data.message)
            html  = u'<html><head></head><body>%s</body>' % (data.message)
            content_html = MIMEText(html, u'html')
            content.attach(content_html)
            content_text = MIMEText(text, u'plain')
            content.attach(content_text)

            #append attachment
            #@see https://docs.python.org/2/library/email-examples.html
            if data.attachment is not None and len(data.attachment)>0:
                #there is something to attach
                #file exists?
                if os.path.isfile(data.attachment):
                    ctype, encoding = mimetypes.guess_type(data.attachment)
                    if ctype is None or encoding is not None:
                        ctype = u'application/octet-stream'
                    maintype, subtype = ctype.split(u'/', 1)
                    if maintype == u'text':
                        fp = open(data.attachment)
                        msg = MIMEText(fp.read(), _subtype=subtype)
                        fp.close()
                    elif maintype == u'image':
                        fp = open(data.attachment, u'rb')
                        msg = MIMEImage(fp.read(), _subtype=subtype)
                        fp.close()
                    elif maintype == u'audio':
                        fp = open(data.attachment, u'rb')
                        msg = MIMEAudio(fp.read(), _subtype=subtype)
                        fp.close()
                    else:
                        fp = open(data.attachment, u'rb')
                        msg = MIMEBase(maintype, subtype)
                        msg.set_payload(fp.read())
                        fp.close()
                        #encode the payload using Base64
                        encoders.encode_base64(msg)
                    #set the filename parameter
                    msg.add_header(u'Content-Disposition', u'attachment', filename=os.path.basename(data.attachment))
                    mail.attach(msg)

            #connect mail server
            smtp_server = None
            if ssl is True:
                self.logger.debug(u'Connect SMTP server with SSL on %s:%s' % (server, port))
                if port is not None:
                    smtp_server = smtplib.SMTP_SSL(server, port)
                else:
                    smtp_server = smtplib.SMTP_SSL(server)
            else:
                self.logger.debug(u'Connect SMTP server without SSL on %s:%s' % (server, port))
                if port is not None:
                    smtp_server = smtplib.SMTP(server, port)
                else:
                    smtp_server = smtplib.SMTP(server)
            smtp_server.set_debuglevel(True)
            if tls is True:
                self.logger.debug(u'StartTLS session')
                smtp_server.starttls()
            if login is not None and len(login)>0:
                self.logger.debug(u'Connect to server using "%s:%s"' % (login, password))
                smtp_server.login(login, password)
            self.logger.debug(u'Connected to server')

            #send email
            smtp_server.sendmail(sender, data.recipients[0], mail.as_string())
            smtp_server.quit()

        except smtplib.SMTPServerDisconnected as e:
            self.logger.exception(u'Failed to send test:')
            raise Exception(u'Server disconnected')

        except smtplib.SMTPSenderRefused as e:
            self.logger.exception(u'Failed to send test:')
            raise Exception(u'Email sender must be a valid email address')

        except smtplib.SMTPRecipientsRefused as e:
            self.logger.exception(u'Failed to send test:')
            raise Exception(u'Some recipients were refused')

        except smtplib.SMTPDataError as e:
            self.logger.exception(u'Failed to send test:')
            raise Exception(u'Problem with email content')

        except smtplib.SMTPConnectError as e:
            self.logger.exception(u'Failed to send test:')
            raise Exception(u'Unable to establish connection with smtp server. Please check server address')

        except smtplib.SMTPAuthenticationError as e:
            self.logger.exception(u'Failed to send test:')
            raise Exception(u'Authentication failed. Please check credentials.')
            
        except Exception as e:
            self.logger.exception(u'Failed to send test:')
            raise Exception('Unable to send email. Please check configuration')

    def __check_and_get_config(self, provider, server, port, login, password, tls, ssl, sender):
        """
        Check and get valid configuration
        """
        #check parameters
        if provider in ('gmail', 'yahoo'):
            if login is None or len(login)==0:
                raise MissingParameter(u'Parameter "login" is missing')
            if password is None or len(password)==0:
                raise MissingParameter(u'Parameter "password" is missing')
        else:
            if server is None or len(server)==0:
                raise MissingParameter(u'Parameter "server" is missing')

        #force some parameters if necessary
        if provider in self.PROVIDERS:
            self.logger.debug(u'Force parameters to configured provider')
            server = self.PROVIDERS[provider][u'server']
            port = self.PROVIDERS[provider][u'port']
            tls = self.PROVIDERS[provider][u'tls']
            ssl = self.PROVIDERS[provider][u'ssl']
            sender = login

        self.logger.debug('Updated parameters: provider=%s server=%s port=%s login=%s password=%s tls=%s ssl=%s sender=%s' % (provider, server, port, login, password, tls, ssl, sender))
        return (provider, server, port, login, password, tls, ssl, sender)

    def set_config(self, provider, server=None, port=None, login=None, password=None, tls=None, ssl=None, sender=None):
        """
        Set configuration

        Params:
            server (string): smtp server address
            port (int): smtp server port
            login (string): login to connect to smtp server
            password (string): password to connect to smtp server
            tls (bool): TLS option
            ssl (bool): SSL option
            sender (string): email sender

        Returns:
            bool: True if config saved successfully
        """
        #check parameters
        (provider, server, port, login, password, tls, ssl, sender) = self.__check_and_get_config(provider, server, port, login, password, tls, ssl, sender)

        #save config
        return self._update_config({
            u'provider': provider,
            u'server': server,
            u'port': port,
            u'login': login,
            u'password': password,
            u'tls': tls,
            u'ssl': ssl,
            u'sender': sender
        })

    def test(self, recipient, provider, server=None, port=None, login=None, password=None, tls=None, ssl=None, sender=None):
        """
        Send test email

        Params:
            recipient (string): email recipient for test
            provider (string): email provider
            server (string): smtp server address
            port (int): smtp server port
            login (string): login to connect to smtp server
            password (string): password to connect to smtp server
            tls (bool): TLS option
            ssl (bool): SSL option
            sender (string): email sender

        Returns:
            bool: True if test succeed
        """
        #check parameters
        if recipient is None or len(recipient)==0:
            raise CommandError(u'Recipient parameter is missing')
        config = self._get_config()
        (provider, server, port, login, password, tls, ssl, sender) = self.__check_and_get_config(provider, server, port, login, password if password is not None else config[u'password'], tls, ssl, sender)

        #prepare data
        data = AlertEmailProfile()
        data.subject = u'Cleep test'
        data.message = u'Hello this is Cleep.\n\nIf you received this message it means your server web configuration is working fine.\n\nEnjoy ;-)'
        data.recipients.append(recipient)

        #send email
        self.__send_email(server, port, login, password, tls, ssl, sender, data)

        return True

    def _render(self, profile):
        """
        Render profile

        Params:
            profile (EmailProfile): EmailProfile instance

        Returns:
            bool: True if post succeed, False otherwise
        """
        config = self._get_config()
        if config[u'server'] is None or len(config[u'server'])==0:
            #not configured
            raise CommandError(u'Can\'t send email because module is not configured')
        (provider, server, port, login, password, tls, ssl, sender) = self.__check_and_get_config(config[u'provider'], config[u'server'], config[u'port'], config[u'login'], config[u'password'], config[u'tls'], config[u'ssl'], config[u'sender'])

        #send email
        self.__send_email(server, port, login, password, tls, ssl, sender, profile)

        return True

