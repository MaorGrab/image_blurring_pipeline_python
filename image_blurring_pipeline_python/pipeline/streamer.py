from multiprocessing import Process

import cv2

from image_blurring_pipeline_python.logger.setup_process_logger import setup_process_logger


class Streamer(Process):
    def __init__(self, input_path, input_queue, log_queue):
        super().__init__()
        self.input_path = input_path
        self.input_queue = input_queue
        self.log_queue = log_queue

    def run(self):
        """
        Reads video frames and puts them into the input_queue.
        """
        logger = setup_process_logger(self.log_queue)

        cap = cv2.VideoCapture(self.input_path)
        if not cap.isOpened():
            logger.error("Failed to open video file: %s", self.input_path)
            return

        frame_id = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

            self.input_queue.put((frame_id, frame, timestamp_ms))
            logger.debug("Enqueued frame %s", frame_id)
            frame_id += 1

        cap.release()
        self.input_queue.put(None)
        logger.info("streamer finished.")
