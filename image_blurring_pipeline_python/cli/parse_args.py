import argparse

def parse_args() -> argparse:
    parser = argparse.ArgumentParser(description="Video analytics pipeline")
    parser.add_argument("--video_path", type=str, help="Path to input video file")
    args = parser.parse_args()
    return args
