"""Generic Class for Python Logging"""
import cgitb
from datetime import datetime
import logging
import requests
import sys

from email_config import MAILGUN, NOTIFICATIONS


class Logger:
    """Python Logger class"""
    __LOGGER = None
    __DEFAULT_FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
    __DEFAULT_LOG_LEVEL = "debug"
    __LOG_LEVELS = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "unset": logging.NOTSET,
    }
    __SEND_ALERT = True

    def __init__(self, name, log_level=__DEFAULT_LOG_LEVEL, log_format=__DEFAULT_FORMAT, send_alerts=__SEND_ALERT):
        """Initializes the logger"""
        self.__SEND_ALERT = send_alerts
        log_level = self.__get_log_level(log_level)
        self.__init_log_file(name, log_level)
        self.__set_log_level(log_level)
        self.__set_log_format(log_format)

    def __enter__(self):
        """Use with for invocation"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Use with for invocation"""
        pass

    def __get_log_level(self, log_level):
        log_level = self.__LOG_LEVELS.get(log_level.lower(), logging.NOTSET)
        return log_level

    def __init_log_file(self, service_name, log_level):
        """Initializes the logger object"""
        self.__SERVICE_NAME = service_name
        self.__LOGGER = logging.getLogger(self.__SERVICE_NAME)
        self.__LOGGER.setLevel(log_level)

    def __set_log_level(self, log_level):
        """Sets the Log level"""
        self.__CONSOLE_HANDLER = logging.StreamHandler(sys.stdout)
        self.__CONSOLE_HANDLER.setLevel(log_level)

    def __set_log_format(self, log_format):
        self.__FORMATTER = logging.Formatter(log_format)
        self.__CONSOLE_HANDLER.setFormatter(self.__FORMATTER)
        self.__LOGGER.addHandler(self.__CONSOLE_HANDLER)

    def _send_mailgun(self, html_data, subject):
        try:
            result = requests.post(
                MAILGUN["url"],
                auth=("api", MAILGUN["api_key"]),
                data={
                    "from": MAILGUN["from"],
                    "to": NOTIFICATIONS,
                    "subject": subject,
                    "html": html_data
                }
            )
        except Exception as e:
            print datetime.utcnow(), ": send_mailgun error :", e.message
            print "Error in sending email. ", e.message
            return False
        else:
            return result

    def _send_stacktrace(self):
        """Sends the stacktrace to the email IDs"""
        error = cgitb.html(sys.exc_info())
        subject = "Exception occurred in service: %s" % self.__SERVICE_NAME
        self._send_mailgun(error, subject)

    @property
    def LOGGER(self):
        """Returns the LOGGER object"""
        return self.__LOGGER

    def info(self, message):
        """Prints info message"""
        self.__LOGGER.info(message)

    def debug(self, message):
        """Prints debug message"""
        self.__LOGGER.debug(message)

    def exception(self, message):
        """Prints exception message and sends stacktrace if enabled"""
        self.__LOGGER.exception(message)
        if self.__SEND_ALERT:
            self._send_stacktrace()

    def error(self, message):
        """Prints error message"""
        self.__LOGGER.error(message)
