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
LOG_LEVEL = logging.DEBUG
LOGGER_NAME = 'image_pipeline'
