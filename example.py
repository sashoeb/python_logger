from app_logger import Logger

LOGGER = Logger(name="test", log_level="debug")
try:
    LOGGER.info("My first log stmt")
    LOGGER.debug(123456)
    raise Exception("Some error in code")
except Exception as e:
    LOGGER.error("Hey this is an error message")
    LOGGER.exception(e)

with Logger(name="test_with", log_level="info") as LOGGER:
    try:
        LOGGER.info("My first log stmt")
        LOGGER.debug(123456)
        raise Exception("Some error in code")
    except Exception as e:
        LOGGER.error("Hey this is an error message")
        LOGGER.exception(e)
