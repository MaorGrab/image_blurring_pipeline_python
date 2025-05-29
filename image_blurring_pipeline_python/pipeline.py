import cv2
import imutils
import time
import logging
import logging.handlers
import multiprocessing
import sys

NUM_WORKERS = 1

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

def setup_worker_logger(log_queue):
    """
    Sets up a logger for worker processes to send logs to the log_queue.
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
    small = cv2.resize(roi, (8, 8), interpolation=cv2.INTER_LINEAR)
    mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    frame[y:y+h, x:x+w] = mosaic
    return frame

def streamer(input_path, input_queue, total_frames, log_queue):
    """
    Reads video frames and puts them into the input_queue.
    """
    setup_worker_logger(log_queue)
    logger = logging.getLogger()

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        logger.error(f"Failed to open video file: {input_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(fps, width, height)

    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        input_queue.put((frame_id, frame))
        logger.info(f"Enqueued frame {frame_id}")
        frame_id += 1

    cap.release()
    input_queue.put(None)
    logger.info('streamer put None')
    logger.info("streamer finished reading video.")
    total_frames.value = frame_id

def worker(input_queue, output_queue, log_queue):
    """
    Processes frames: detects contours and applies mosaic.
    """
    setup_worker_logger(log_queue)
    logger = logging.getLogger()

    prev_frame = None

    while True:
        item = input_queue.get()
        if item is None:
            logger.info('Worker got item None')
            break
        frame_id, frame = item
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is None:
            prev_frame = gray_frame
            continue
        contours = get_contours(gray_frame, prev_frame)
        prev_frame = gray_frame
        for contour in contours:
            peri = cv2.arcLength(contour,True)
            apprx = cv2.approxPolyDP(contour, 0.1*peri, True)
            x,y,w,h = cv2.boundingRect(apprx)
            # frame = mosaic_roi(frame, x, y, w, h)
            if frame is None:
                continue
        output_queue.put((frame_id, frame))
        logger.info(f"Worker processed frame {frame_id}")
    output_queue.put(None)

def displayer(output_path, output_queue, total_frames, log_queue):
    """
    Writes processed frames to the output video file.
    """
    setup_worker_logger(log_queue)
    logger = logging.getLogger()

    buffer = {}  # frame_id: frame
    next_frame_id_to_record = 0

    # Assuming frame properties are known; adjust as needed
    ##############
    cap = cv2.VideoCapture('data/example.mp4')
    if not cap.isOpened():
        print("Error opening video file")
        return

    # Get frame properties
    # fps = cap.get(cv2.CAP_PROP_FPS)
    # width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    # cap.release()
    ##############
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 25.0
    width, height = 1280, 720
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    num_workers_left = NUM_WORKERS

    while True:
        logger.info(f'[displayer] consuming')
        item = output_queue.get()
        if item is None:
            num_workers_left -= 1
            logger.info(f'[displayer] item is None. Workers left: {num_workers_left}')
            if not num_workers_left:
                break
            continue
        frame_id, frame = item
        if frame_id == next_frame_id_to_record:
            out.write(frame)
            next_frame_id_to_record += 1
            logger.info(f"wrote frame {frame_id}")
        else:
            buffer[frame_id] = frame
            logger.info(f"buffered frame {frame_id}")

        # cv2.imshow('Censored Video', frame)

        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

        while next_frame_id_to_record in buffer:
            out.write(buffer.pop(next_frame_id_to_record))
            logger.info(f"wrote frame {next_frame_id_to_record} from buffer")
            next_frame_id_to_record += 1

    out.release()
    logger.info("displayer finished writing video.")
    # cv2.destroyAllWindows()

def main(input_video_path, output_video_path):
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()
    log_queue = manager.Queue()
    total_frames = manager.Value('i', 0)

    setup_worker_logger(log_queue)
    logger = logging.getLogger()

    logger_proc = multiprocessing.Process(target=logger_process, args=(log_queue,))
    logger_proc.start()
    logger.info('logger process started')

    streamer_proc = multiprocessing.Process(target=streamer, args=(input_video_path, input_queue, total_frames, log_queue))
    streamer_proc.start()
    logger.info('streamer process started')

    num_workers = NUM_WORKERS
    workers = []
    for _ in range(num_workers):
        p = multiprocessing.Process(target=worker, args=(input_queue, output_queue, log_queue))
        p.start()
        logger.info('worker process started')
        workers.append(p)

    displayer_proc = multiprocessing.Process(target=displayer, args=(output_video_path, output_queue, total_frames, log_queue))
    displayer_proc.start()
    logger.info('displayer process started')

    logger.info('streamer_proc.join()')
    streamer_proc.join()
    logger.info('streamer_proc.join() - finished')
    for _ in range(num_workers):
        input_queue.put(None)
    for p in workers:
        logger.info('p.join()')
        p.join()
        logger.info('p.join() - finished')
    logger.info('displayer_proc.join()')
    displayer_proc.join()
    logger.info('displayer_proc.join() - finished')
    log_queue.put(None)
    logger.info('logger_proc.join()')
    logger_proc.join()
    logger.info('logger_proc.join() - finished')


if __name__ == '__main__':
    INPUT_VIDEO = 'data/example.mp4'
    OUTPUT_VIDEO = INPUT_VIDEO.replace('.', '_censored_mp.')

    main(INPUT_VIDEO, OUTPUT_VIDEO)
