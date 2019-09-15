"""Generic Class for Python Logging"""
import cgitb
from datetime import datetime
from functools import wraps
import logging
import requests
import socket
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
    __IS_SERVICE = False
    __INSTANCE = socket.gethostname()


    def __init__(self, name, log_level=__DEFAULT_LOG_LEVEL, log_format=__DEFAULT_FORMAT, send_alerts=__SEND_ALERT,
                 is_service=__IS_SERVICE, instance=__INSTANCE):
        """Initializes the logger"""
        self.__INSTANCE = instance
        if is_service:
            subject = "[%s] Service: %s started" % (instance, name)
            email = "<body><p>Service %s has started at: %s UTC</p></body>" % (name, str(datetime.utcnow()))
            self._send_mailgun(email, subject)

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
        self.__LOGGER = logging.Logger(self.__SERVICE_NAME, log_level)
        self.info = self.__LOGGER.info
        self.debug = self.__LOGGER.debug
        self.error = self.__LOGGER.error
        self.warning = self.__LOGGER.warning

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
            self.__LOGGER.error("Error in sending email. Exception : %s " % e.message)
            return False
        else:
            return result

    def _send_stacktrace(self):
        """Sends the stacktrace to the email IDs"""
        error = cgitb.html(sys.exc_info())
        subject = "[%s] Exception occurred in service: %s" % (self.__INSTANCE, self.__SERVICE_NAME)
        self._send_mailgun(error, subject)

    def protect_method(self, method=None, exception_response=None):
        """Returns a wrapper function which adds the try and catch block to the supplied method.
        If exception is raised in supplied func, then exception response is returned.
        """
        def override_exception_return(protected_method):
            @wraps(protected_method)
            def print_method_access(*args, **kwargs):
                method_response = exception_response
                try:
                    method_response = protected_method(*args, **kwargs)
                except Exception as e:
                    self.exception(e)
                return method_response
            print_method_access.__name__ = protected_method.__name__
            return print_method_access
        if not method:
            return override_exception_return
        override_exception_return.__name__ = method.__name__
        return override_exception_return(protected_method=method)

    @property
    def LOGGER(self):
        """Returns the LOGGER object"""
        return self.__LOGGER

    def exception(self, message):
        """Prints exception message and sends stacktrace if enabled"""
        self.__LOGGER.exception(message)
        if self.__SEND_ALERT:
            self._send_stacktrace()
