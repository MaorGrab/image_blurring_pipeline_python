import cv2
import imutils
from datetime import datetime, timedelta
from multiprocessing import Process
from image_blurring_pipeline_python.logger.setup_process_logger import setup_process_logger

MIN_DETECTION_AREA = 25

class Displayer(Process):
    def __init__(self, output_queue, log_queue):
        super().__init__()
        self.output_queue = output_queue
        self.log_queue = log_queue

    def run(self):
        """
        Writes processed frames to the output video file.
        """
        self.logger = setup_process_logger(self.log_queue)

        buffer = {}  # frame_id: frame
        next_frame_id_to_record = 0


        while True:
            self.logger.info(f'[displayer] consuming')
            item = self.output_queue.get()
            if item is None:
                self.logger.info(f'[displayer] item is None. breaking')
                break
            frame_id, frame, timestamp_ms, contours = item
            if frame_id == next_frame_id_to_record:
                self._alter_image_and_display(frame, timestamp_ms, contours)
                next_frame_id_to_record += 1
                self.logger.info(f"wrote frame {frame_id}")
            else:
                buffer[frame_id] = frame
                self.logger.info(f"buffered frame {frame_id}")

            while next_frame_id_to_record in buffer:
                self._alter_image_and_display(frame, timestamp_ms, contours)
                self.logger.info(f"wrote frame {next_frame_id_to_record} from buffer")
                next_frame_id_to_record += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        self.logger.info("displayer finished writing video.")
        cv2.destroyAllWindows()

    def _alter_image_and_display(self, frame, timestamp_ms, contours):
        for contour in contours:
            x,y,w,h = cv2.boundingRect(contour)
            if w * h > MIN_DETECTION_AREA:
                frame = self._mosaic_roi(frame, x, y, w, h)
        timestamp = self._get_timestamp_in_format(timestamp_ms)
        cv2.putText(frame, timestamp, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow('Censored Video', frame)

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
