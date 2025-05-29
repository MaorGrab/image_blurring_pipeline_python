from multiprocessing import Process
import logging
import sys

from image_blurring_pipeline_python.config import constants

class Logger(Process):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def run(self):
        """
        Logger process that receives log records from the log_queue and logs them.
        """
        logger = logging.Logger(name=constants.LOGGER_NAME)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(asctime)s] [%(processName)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(constants.LOG_LEVEL)

        while True:
            record = self.log_queue.get()
            if record is None:
                logger.debug('logger got a None and stopped logging')
                break
            logger.handle(record)
