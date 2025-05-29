import logging
import logging.handlers

def setup_process_logger(log_queue) -> logging.Logger:
    """
    Sets up a logger for a processes to send logs to the log_queue.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(handler)
    return logger
