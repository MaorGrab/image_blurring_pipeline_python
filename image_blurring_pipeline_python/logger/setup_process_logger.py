import logging
import logging.handlers

from image_blurring_pipeline_python.config import constants

def setup_process_logger(log_queue) -> logging.Logger:
    """
    Sets up a logger for a processes to send logs to the log_queue.
    """
    logger = logging.getLogger(name=constants.LOGGER_NAME)
    logger.setLevel(constants.LOG_LEVEL)
    handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(handler)
    return logger
