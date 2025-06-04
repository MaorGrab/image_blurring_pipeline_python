import logging
from pathlib import Path

# paths
PKG_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = PKG_DIR.parent
SAMPLE_DATA_PATH = ROOT_DIR / 'data' / 'example.mp4'

# displayer
MIN_DETECTION_AREA = 25
DISPLAY_BOUNDING_BOXES = True

# logger
LOG_LEVEL = logging.INFO
LOG_FILE_LEVEL = logging.DEBUG
LOG_FILE_NAME = 'image_pipeline.log'
LOG_DIR = ROOT_DIR / 'logs'
LOG_PATH = LOG_DIR / LOG_FILE_NAME
