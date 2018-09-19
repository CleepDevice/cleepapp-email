#!/usr/bin/env python
# -*- coding: utf-8 -*-

from raspiot.events.formatter import Formatter
from raspiot.events.alertEmailProfile import AlertEmailProfile

class AlertEmailSendToEmailFormatter(Formatter):
    """
    Email data to EmailProfile
    """
    def __init__(self, events_factory):
        """
        Constuctor

        Args:
            events_factory (EventsFactory): events factory instance
        """
        Formatter.__init__(self, events_factory, u'alert.email.send', AlertEmailProfile())

    def _fill_profile(self, event_values, profile):
        """
        Fill profile with event data
        """
        profile.subject = event_values[u'subject']
        profile.message = event_values[u'message']
        profile.attachment = event_values[u'attachment']
        profile.recipients = event_values[u'recipients']

        return profile

