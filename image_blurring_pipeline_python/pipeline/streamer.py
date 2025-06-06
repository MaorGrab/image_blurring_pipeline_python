from multiprocessing import Process, Queue
from pathlib import Path

import cv2

from image_blurring_pipeline_python.models.queue_items import InputItem
from image_blurring_pipeline_python.logger.logger_manager import configure_process_logger


class Streamer(Process):
    def __init__(self, input_path: Path, input_queue: Queue, log_queue: Queue) -> None:
        super().__init__()
        self.input_path: Path = input_path
        self.input_queue: Queue = input_queue
        self.log_queue: Queue = log_queue

    def run(self) -> None:
        """
        Reads video frames and puts them into the input_queue.
        """
        logger = configure_process_logger(self.log_queue)

        cap = cv2.VideoCapture(self.input_path)
        if not cap.isOpened():
            self.input_queue.put(None)
            logger.error("Failed to open video file: %s", self.input_path)
            return

        frame_id: int = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            timestamp_ms: int = cap.get(cv2.CAP_PROP_POS_MSEC)

            input_item = InputItem(frame=frame, frame_id=frame_id, timestamp_ms=timestamp_ms)
            self.input_queue.put(input_item)
            logger.debug("Enqueued frame %s", frame_id)
            frame_id += 1

        cap.release()
        self.input_queue.put(InputItem.termination())
        logger.info("streamer finished.")
