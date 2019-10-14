import unittest
import logging
import sys
sys.path.append('../')
from backend.smtp import Smtp
from raspiot.utils import InvalidParameter, MissingParameter, CommandError, Unauthorized
from raspiot.libs.tests import session
import os
import time
from mock import Mock

class TestSmtp(unittest.TestCase):

    def setUp(self):
        self.session = session.TestSession(logging.CRITICAL)
        _smtp = Smtp
        self.module = self.session.setup(_smtp)

    def tearDown(self):
        self.session.clean()

if __name__ == "__main__":
    unittest.main()
    
