import sys
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

def my_err_handler(traceback, exec_info):
    """A custom function to handle the errors
    This function receives two arguments, i.e. traceback and system exec info
    """
    print "Custom function invoked"
    print "Formatted exception"
    print traceback.format_exc()
    print "System exec info"
    print exec_info
    exp_type, exp_value, exp_traceback = exec_info
    print "String formatted exception"
    print traceback.format_exception(exp_type, exp_value, exp_traceback)
    print "End of custom function"

with Logger(name="CUSTOM_ERROR_HANDLER", send_alerts=True) as LOGGER:
    try:
        LOGGER.info("Custom error handling example")
        LOGGER.debug("Will execute a function given by you in case of exception")
        if not LOGGER.set_custom_error_handler(my_err_handler):
            LOGGER.error("Unable to set custom error handler")
            sys.exit(0)
        LOGGER.debug("Divide by zero error")
        a = 0 / 0  # Will print the divide by zero error message
    except Exception as e:
        LOGGER.error("Encountered error second_example_app")
        LOGGER.exception(e)

    try:
        LOGGER.debug("Type error")
        "2" + 2
    except Exception as e:
        LOGGER.error("Encountered error second_example_app")
        LOGGER.exception(e)
