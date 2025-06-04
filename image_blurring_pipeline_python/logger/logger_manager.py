from multiprocessing import Queue
import logging
import logging.handlers
import sys
import os

from image_blurring_pipeline_python.config import constants


class LoggerManager:
    def __init__(self):
        self.log_queue = Queue()
        self.listener = None

    def start_listener(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '[%(asctime)s] [%(processName)s] - %(levelname)s: %(message)s'
        )

        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(constants.LOG_LEVEL)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        os.makedirs(constants.LOG_DIR, exist_ok=True)
        if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
            file_handler = logging.FileHandler(constants.LOG_PATH)
            file_handler.setLevel(constants.LOG_FILE_LEVEL)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        self.listener = logging.handlers.QueueListener(
            self.log_queue,
            *root_logger.handlers,
            respect_handler_level=True,
        )
        self.listener.start()

    def stop_listener(self):
        if self.listener:
            self.listener.stop()
        self.log_queue.close()
        self.log_queue.join_thread()

    def get_queue(self):
        return self.log_queue


def configure_process_logger(log_queue: Queue, logger_name: str = 'process-logger'):
    logger = logging.getLogger(logger_name)
    if logger.handlers:  # already exists, no need to define it
        return logger
    logger.setLevel(logging.DEBUG)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(queue_handler)
    logger.propagate = False
    return logger
