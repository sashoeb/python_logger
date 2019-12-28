"""Generic Class for Python Logging"""
import cgitb
from datetime import datetime
from functools import wraps
import json
import logging
import paho.mqtt.client as mqtt
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
    __CUSTOM_ERR_HANDLER = None


    def __init__(self, name, log_level=__DEFAULT_LOG_LEVEL, log_format=__DEFAULT_FORMAT, send_alerts=__SEND_ALERT,
                 is_service=__IS_SERVICE, instance=__INSTANCE):
        """Initializes the logger"""
        self.__INSTANCE = instance
        self.__logger_name = name
        if is_service:
            subject = "[%s] Service: %s started" % (instance, name)
            email = "<body><p>Service %s has started at: %s UTC</p></body>" % (name, str(datetime.utcnow()))
            self._send_mailgun(email, subject)

        self.__SEND_ALERT = send_alerts
        log_level = self.__get_log_level(log_level)
        self.__init_log_file(name, log_level)
        self.__set_log_level(log_level)
        self.__set_log_format(log_format)
        self.is_remote_control_enabled = False
        self.available_functions = {
            "disconnect": self.disable_remote_control,
            "test": self.my_func
        }

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
        if self.__mqtt_client:
            self.__mqtt_client.publish(self.__topic, json.dumps({"status": "exception", "message": str(message)}))
        if self.__SEND_ALERT and not self.__CUSTOM_ERR_HANDLER:
            self._send_stacktrace()
        if self.__CUSTOM_ERR_HANDLER:
            func_name = self.__CUSTOM_ERR_HANDLER.__name__
            self.__LOGGER.debug("Executing custom error handler %s" % func_name)
            traceback = cgitb.traceback
            exec_info = sys.exc_info()
            self.__CUSTOM_ERR_HANDLER(traceback, exec_info)
            self.__LOGGER.debug("Executed custom error handler")

    def set_custom_error_handler(self, func):
        """Sets a custom handler to be executed during exception.
        The function should accept two arguments traceback and exec_info.
        Returns True if able to set else False.
        """
        self.__LOGGER.debug("Setting custom error handler")
        if not callable(func):
            self.__LOGGER.error("NEED A FUNCTION AS AN ARGUMENT")
            self.__LOGGER.error("CUSTOM ERROR HANDLER NOT SET")
            return False
        self.__CUSTOM_ERR_HANDLER = func
        self.__LOGGER.debug("Custom error handler set")
        return True

    def enable_remote_control(self, remote_server_ip, remote_control_key, user_name=None, password=None):
        """Enables control via a remote server"""
        self.__LOGGER.info("Enabling remote control. Server IP: %s Key: %s" % (remote_server_ip, remote_control_key))
        self.__topic = "remote_logger/" + self.__INSTANCE + "/" + self.__logger_name + "/" + remote_control_key
        print "Topic:", self.__topic
        self.__mqtt_client = mqtt.Client(self.__topic)
        print "client", self.__mqtt_client
        if user_name and password:
            self.__mqtt_client.username_pw_set(user_name, password)
        self.__mqtt_client.connect_async(host=remote_server_ip, port=1883, keepalive=10)
        self.__mqtt_client.on_connect = self.__establish_connection
        self.__mqtt_client.on_message = self.on_message
        self.__mqtt_client.enable_logger(logger=self.__LOGGER)
        self.__mqtt_client.loop_start()

    def disable_remote_control(self):
        """Disables the remote control fuctionality"""
        if not self.__mqtt_client:
            return True
        self.__mqtt_client.disconnect()
        self.is_remote_control_enabled = False

    def __establish_connection(self, client, userdata, flags, rc):
        print "establishing connection"
        print "topic: ", self.__topic
        client.subscribe(self.__topic)
        print "user data", userdata
        type(userdata)
        print "flags", flags
        type(flags)
        print "result code", rc
        type(rc)
        self.is_remote_control_enabled = True

    def on_message(self, client, userdata, msg):
        print "*" * 15
        print "received message"
        print msg.topic, ": ", msg.payload, type(msg.payload)
        print "user data: ", userdata
        payload = json.loads(msg.payload)
        function = payload.get("function", None)
        if function:
            if function in self.available_functions.has_key(function):
                function(payload)
        print "*" * 15

    def my_func(self, payload):
        """Custom function"""
        print "my func called"
        print "This is the payload", payload
