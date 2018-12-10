from app_logger import Logger

LOGGER = Logger(name="example_app", log_level="debug", send_alerts=False)
try:
    LOGGER.info("This is an info statement.")
    LOGGER.debug("This is a debug statement with a value: %s" % str(123.456))
except Exception as e:
    LOGGER.error("Encountered an error in example_app")
    LOGGER.exception(e)

with Logger(name="second_example_app") as LOGGER:
    try:
        LOGGER.info("This is also an info statement")
        LOGGER.debug(123456)
        a = 0/0                                     # Will print the divide by zero error message
    except Exception as e:
        LOGGER.error("Encountered error second_example_app")
        LOGGER.exception(e)
