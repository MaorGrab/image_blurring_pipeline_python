from multiprocessing import Process
import logging
import sys

class Logger(Process):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue


    def run(self):
        """
        Logger process that receives log records from the log_queue and logs them.
        """
        logger = logging.getLogger()
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(asctime)s] [%(processName)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        while True:
            record = self.log_queue.get()
            if record is None:
                print('logger got a None and stopped logging')
                break
            logger.handle(record)
