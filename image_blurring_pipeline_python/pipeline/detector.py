from multiprocessing import Process

import cv2
import imutils

from image_blurring_pipeline_python.logger.logger_manager import configure_process_logger


class Detector(Process):
    def __init__(self, input_queue, output_queue, log_queue):
        super().__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.log_queue = log_queue

    def run(self):
        """
        Processes frames: detects contours and puts them in the output queue.
        """
        logger = configure_process_logger(self.log_queue)

        prev_frame = None

        while True:
            item = self.input_queue.get()
            if item is None:
                logger.debug('detector got item None')
                break
            frame_id, frame, timestamp_ms = item
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if prev_frame is None:  # handle first frame
                self.output_queue.put((frame_id, frame, timestamp_ms, ()))
                prev_frame = gray_frame
                continue
            contours = self._get_contours(gray_frame, prev_frame)
            prev_frame = gray_frame
            self.output_queue.put((frame_id, frame, timestamp_ms, contours))
            logger.debug("detector processed frame %s", frame_id)
        self.output_queue.put(None)
        logger.info("detector finished.")

    @staticmethod
    def _get_contours(current_frame, prev_frame) -> tuple:
        diff = cv2.absdiff(current_frame, prev_frame)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return imutils.grab_contours(cnts)
