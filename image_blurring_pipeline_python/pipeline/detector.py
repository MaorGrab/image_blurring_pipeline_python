from multiprocessing import Process, Queue
from typing import Union

import numpy as np
import cv2
import imutils

from image_blurring_pipeline_python.models.queue_items import InputItem, OutputItem
from image_blurring_pipeline_python.logger.logger_manager import configure_process_logger


class Detector(Process):
    def __init__(self, input_queue: Queue, output_queue: Queue, log_queue: Queue) -> None:
        super().__init__()
        self.input_queue: Queue = input_queue
        self.output_queue: Queue = output_queue
        self.log_queue: Queue = log_queue

    def run(self) -> None:
        """
        Processes frames: detects contours and puts them in the output queue.
        """
        logger = configure_process_logger(self.log_queue)

        prev_frame: Union[np.ndarray, None] = None

        while True:
            input_item: InputItem = self.input_queue.get()
            if input_item.is_termination:
                logger.debug('detector got termination item')
                break
            output_item = OutputItem(
                frame=input_item.frame,
                frame_id=input_item.frame_id,
                timestamp_ms=input_item.timestamp_ms,
                contours=tuple(),
            )
            gray_frame: np.ndarray = cv2.cvtColor(input_item.frame, cv2.COLOR_BGR2GRAY)
            if prev_frame is None:  # handle first frame
                self.output_queue.put(output_item)
                prev_frame = gray_frame
                continue
            output_item.contours = self._get_contours(gray_frame, prev_frame)
            self.output_queue.put(output_item)
            prev_frame = gray_frame
            logger.debug("detector processed frame %s", input_item.frame_id)
        self.output_queue.put(OutputItem.termination())
        logger.info("detector finished.")

    @staticmethod
    def _get_contours(current_frame, prev_frame) -> tuple:
        diff = cv2.absdiff(current_frame, prev_frame)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return imutils.grab_contours(cnts)
