from app_logger import Logger

LOGGER = Logger(name="example_app", log_level="debug")
try:
    LOGGER.info("This is an info statement.")
    LOGGER.debug("This is a debug statement with a value: %s" % str(123.456))
    raise Exception("Example error")
except Exception as e:
    LOGGER.error("This is an error message.")
    LOGGER.exception(e)

with Logger(name="second_example_app", log_level="error") as LOGGER:
    try:
        LOGGER.info("This info statement won't be printed")
        LOGGER.debug(123456)
        a = 0/0                                     # Will print the divide by zero error message
    except Exception as e:
        LOGGER.error("This is the error message for divide by zero error")
        LOGGER.exception(e)
