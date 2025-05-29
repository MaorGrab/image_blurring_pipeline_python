import cv2
from multiprocessing import Process
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
        self.logger = setup_process_logger(self.log_queue)

        cap = cv2.VideoCapture(self.input_path)
        if not cap.isOpened():
            self.logger.error(f"Failed to open video file: {self.input_path}")
            return
        
        frame_id = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

            self.input_queue.put((frame_id, frame, timestamp_ms))
            self.logger.info(f"Enqueued frame {frame_id}")
            frame_id += 1

        cap.release()
        self.input_queue.put(None)
        self.logger.info("streamer finished reading video.")