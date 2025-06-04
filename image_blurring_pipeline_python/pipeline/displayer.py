from datetime import datetime, timedelta
from multiprocessing import Process

import cv2

from image_blurring_pipeline_python.config import constants
from image_blurring_pipeline_python.models.queue_items import OutputItem
from image_blurring_pipeline_python.logger.logger_manager import configure_process_logger


class Displayer(Process):
    def __init__(self, output_queue, log_queue):
        super().__init__()
        self.output_queue = output_queue
        self.log_queue = log_queue

    def run(self):
        """
        Displays processed frames.
        """
        logger = configure_process_logger(self.log_queue)

        buffer = {}  # frame_id: frame
        next_frame_id_to_record = 0

        while True:
            output_item: OutputItem = self.output_queue.get()
            if output_item.is_termination:
                logger.debug('displayer got termination item')
                break
            if output_item.frame_id == next_frame_id_to_record:
                self._alter_image_and_display(output_item)
                next_frame_id_to_record += 1
                logger.debug("displayed frame %s", output_item.frame_id)
            else:  # buffer frame if it didn't arrive at the expected order
                buffer[output_item.frame_id] = output_item
                logger.debug("buffered frame %s", output_item.frame_id)

            while next_frame_id_to_record in buffer:  # keep outputing buffered frames in order
                buffered_item = buffer.pop(next_frame_id_to_record)
                self._alter_image_and_display(buffered_item)
                logger.debug("wrote frame %s from buffer", next_frame_id_to_record)
                next_frame_id_to_record += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        logger.info("displayer finished.")
        cv2.destroyAllWindows()

    def _alter_image_and_display(self, output_item: OutputItem):
        frame = output_item.frame
        for contour in output_item.contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w * h > constants.MIN_DETECTION_AREA:
                frame = self._mosaic_roi(frame, x, y, w, h)
            if constants.DISPLAY_BOUNDING_BOXES:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
        timestamp = self._get_timestamp_in_format(output_item.timestamp_ms)
        cv2.putText(frame, timestamp, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow('Blurred Video', frame)

    @staticmethod
    def _mosaic_roi(frame, x, y, w, h):
        roi = frame[y:y+h, x:x+w]
        # Resize to tiny then back up = pixelation
        small = cv2.resize(roi, (4, 4), interpolation=cv2.INTER_LINEAR)
        mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        frame[y:y+h, x:x+w] = mosaic
        return frame

    @staticmethod
    def _get_timestamp_in_format(timestamp_ms):
        return (datetime.min + timedelta(milliseconds=timestamp_ms)).strftime('%H:%M:%S.%f')[:-3]
