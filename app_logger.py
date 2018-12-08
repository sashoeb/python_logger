"""Generic Class for Python Logging"""
import logging
import sys


class Logger:
    """Python Logger class"""
    __LOGGER = None
    __DEFAULT_FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
    __DEFAULT_LOG_LEVEL = "info"
    __LOG_LEVELS = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "unset": logging.NOTSET,
    }

    def __init__(self, name, log_level=__DEFAULT_LOG_LEVEL, log_format=__DEFAULT_FORMAT):
        """Initializes the logger"""
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
        self.__LOGGER = logging.getLogger(service_name)
        self.__LOGGER.setLevel(log_level)

    def __set_log_level(self, log_level):
        """Sets the Log level"""
        self.__CONSOLE_HANDLER = logging.StreamHandler(sys.stdout)
        self.__CONSOLE_HANDLER.setLevel(log_level)

    def __set_log_format(self, log_format):
        self.__FORMATTER = logging.Formatter(log_format)
        self.__CONSOLE_HANDLER.setFormatter(self.__FORMATTER)
        self.__LOGGER.addHandler(self.__CONSOLE_HANDLER)

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
        """Prints exception message"""
        self.__LOGGER.exception(message)

    def error(self, message):
        """Prints error message"""
        self.__LOGGER.error(message)