import multiprocessing

from image_blurring_pipeline_python.pipeline.streamer import Streamer
from image_blurring_pipeline_python.pipeline.detector import Detector
from image_blurring_pipeline_python.pipeline.displayer import Displayer
from image_blurring_pipeline_python.logger.logger import Logger
from image_blurring_pipeline_python.logger.setup_process_logger import setup_process_logger

def main(input_video_path):
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()
    log_queue = manager.Queue()


    logger_proc = Logger(log_queue)
    logger_proc.start()

    logger = setup_process_logger(log_queue)
    logger.info('logger process started')

    streamer_proc = Streamer(input_video_path, input_queue, log_queue)
    streamer_proc.start()
    logger.info('streamer process started')

    detector_proc = Detector(input_queue, output_queue, log_queue)
    detector_proc.start()
    logger.info('detector process started')

    displayer_proc = Displayer(output_queue, log_queue)
    displayer_proc.start()
    logger.info('displayer process started')

    logger.info('streamer_proc.join()')
    streamer_proc.join()
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
