import cv2
import imutils
import time
import logging
import logging.handlers
import multiprocessing
import sys
from datetime import datetime, timedelta


MIN_DETECTION_AREA = 25

def logger_process(log_queue):
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
        record = log_queue.get()
        if record is None:
            print('logger got a None and stopped logging')
            break
        logger.handle(record)

def setup_process_logger(log_queue):
    """
    Sets up a logger for a processes to send logs to the log_queue.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(handler)

def get_contours(current_frame, prev_frame) -> tuple:
    diff = cv2.absdiff(current_frame, prev_frame)
    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return imutils.grab_contours(cnts)

def mosaic_roi(frame, x, y, w, h):
    roi = frame[y:y+h, x:x+w]
    # Resize to tiny then back up = pixelation
    small = cv2.resize(roi, (4, 4), interpolation=cv2.INTER_LINEAR)
    mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    frame[y:y+h, x:x+w] = mosaic
    return frame

def get_timestamp_in_format(timestamp_ms):
    return (datetime.min + timedelta(milliseconds=timestamp_ms)).strftime('%H:%M:%S.%f')[:-3]

def streamer(input_path, input_queue, log_queue):
    """
    Reads video frames and puts them into the input_queue.
    """
    setup_process_logger(log_queue)
    logger = logging.getLogger()

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        logger.error(f"Failed to open video file: {input_path}")
        return
    
    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

        input_queue.put((frame_id, frame, timestamp_ms))
        logger.info(f"Enqueued frame {frame_id}")
        frame_id += 1

    cap.release()
    input_queue.put(None)
    logger.info("streamer finished reading video.")

def detector(input_queue, output_queue, log_queue):
    """
    Processes frames: detects contours and applies mosaic.
    """
    setup_process_logger(log_queue)
    logger = logging.getLogger()

    prev_frame = None

    while True:
        item = input_queue.get()
        if item is None:
            logger.info('detector got item None')
            break
        frame_id, frame, timestamp_ms = item
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is None:
            output_queue.put((frame_id, frame, timestamp_ms, ()))
            prev_frame = gray_frame
            continue
        contours = get_contours(gray_frame, prev_frame)
        prev_frame = gray_frame
        output_queue.put((frame_id, frame, timestamp_ms, contours))
        logger.info(f"detector processed frame {frame_id}")
    output_queue.put(None)

def displayer(output_queue, log_queue):
    """
    Writes processed frames to the output video file.
    """
    setup_process_logger(log_queue)
    logger = logging.getLogger()

    buffer = {}  # frame_id: frame
    next_frame_id_to_record = 0


    while True:
        logger.info(f'[displayer] consuming')
        item = output_queue.get()
        if item is None:
            logger.info(f'[displayer] item is None. breaking')
            break
        frame_id, frame, timestamp_ms, contours = item
        if frame_id == next_frame_id_to_record:
            _alter_image_and_display(frame, timestamp_ms, contours)
            next_frame_id_to_record += 1
            logger.info(f"wrote frame {frame_id}")
        else:
            buffer[frame_id] = frame
            logger.info(f"buffered frame {frame_id}")

        while next_frame_id_to_record in buffer:
            _alter_image_and_display(frame, timestamp_ms, contours)
            logger.info(f"wrote frame {next_frame_id_to_record} from buffer")
            next_frame_id_to_record += 1

        if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    logger.info("displayer finished writing video.")
    cv2.destroyAllWindows()

def _alter_image_and_display(frame, timestamp_ms, contours):
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        if w * h > MIN_DETECTION_AREA:
            frame = mosaic_roi(frame, x, y, w, h)
    timestamp = get_timestamp_in_format(timestamp_ms)
    cv2.putText(frame, timestamp, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imshow('Censored Video', frame)

def main(input_video_path):
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()
    log_queue = manager.Queue()

    setup_process_logger(log_queue)
    logger = logging.getLogger()

    logger_proc = multiprocessing.Process(target=logger_process, args=(log_queue,))
    logger_proc.start()
    logger.info('logger process started')

    streamer_proc = multiprocessing.Process(target=streamer, args=(input_video_path, input_queue, log_queue))
    streamer_proc.start()
    logger.info('streamer process started')

    detector_proc = multiprocessing.Process(target=detector, args=(input_queue, output_queue, log_queue))
    detector_proc.start()
    logger.info('detector process started')

    displayer_proc = multiprocessing.Process(target=displayer, args=(output_queue, log_queue))
    displayer_proc.start()
    logger.info('displayer process started')

    logger.info('streamer_proc.join()')
    streamer_proc.join()
    # input_queue.put(None)
    logger.info('streamer_proc.join() - finished')

    logger.info('detector_proc.join()')
    detector_proc.join()
    logger.info('detector_proc.join() - finished')

    logger.info('displayer_proc.join()')
    displayer_proc.join()
    logger.info('displayer_proc.join() - finished')

    # kill log process
    log_queue.put(None)


if __name__ == '__main__':
    INPUT_VIDEO = 'data/example.mp4'
    main(INPUT_VIDEO)
