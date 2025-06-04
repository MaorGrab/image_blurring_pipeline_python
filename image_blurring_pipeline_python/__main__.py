import multiprocessing

from image_blurring_pipeline_python.pipeline.streamer import Streamer
from image_blurring_pipeline_python.pipeline.detector import Detector
from image_blurring_pipeline_python.pipeline.displayer import Displayer
from image_blurring_pipeline_python.logger.logger_manager import (
    LoggerManager, configure_process_logger
)
from image_blurring_pipeline_python.config import constants
from image_blurring_pipeline_python.cli.parse_args import parse_args

def main(input_video_path):
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()

    logger_manager = LoggerManager()
    logger_manager.start_listener()
    logger = configure_process_logger(logger_manager.get_queue())
    logger.info('logger process started')

    streamer_proc = Streamer(input_video_path, input_queue, logger_manager.get_queue())
    streamer_proc.start()
    logger.info('streamer process started')

    detector_proc = Detector(input_queue, output_queue, logger_manager.get_queue())
    detector_proc.start()
    logger.info('detector process started')

    displayer_proc = Displayer(output_queue, logger_manager.get_queue())
    displayer_proc.start()
    logger.info('displayer process started')

    streamer_proc.join()
    detector_proc.join()
    displayer_proc.join()

    # kill log process
    logger_manager.stop_listener()


if __name__ == '__main__':
    args = parse_args()
    input_data_path = args.video_path if args.video_path else constants.SAMPLE_DATA_PATH
    main(input_data_path)
