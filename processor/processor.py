"""
This is the processor that digests the raw data from MLX90640 and analyzes it.
"""

import argparse
import numpy as np

from xpython.common import files, logger


class MLX90640RawFrame(logger.LoggingClass):
    """RAW binary frame straight out from MLX90640
    This is an array of floats, with 32x24 elements (MLX90640 pixels)
    """

    PIXELS_X        = 32
    PIXELS_Y        = 24
    PIXELS_FRAME    = PIXELS_X * PIXELS_Y

    def __init__(self, frame):
        """Default constructor
        data - array with the pixel data
        """
        self.frame = frame


class MLX90640RawDataProcessor(logger.LoggingClass):
    """RAW binary data file processor
    This class processes the raw binary data as gathered from MLX90640.
    Frames are suppossed to be stored sequentially within the file, at a rate of FPS
    frames per second. The value of FPS determines the time distance in between frames.
    """

    def __init__(self, fps, raw_filepath):
        """Default constructor
        fps - frames per second, necessary to calculate the timeline
        raw_filepath - path to the binary file with the RAW frames
        """
        self.fps = fps
        self.raw_filepath = raw_filepath
        self.sequence = []

    def process(self):
        """
        This method processes the given file, where the RAW data is supposed to be stored.
        """
        with open(self.raw_filepath, mode='r') as f:
            pass

    @staticmethod
    def create(argv):
        # Basic class static factory method.

        parser = argparse.ArgumentParser(description="Process a file with raw data from MLX90640")
        parser.add_argument(
            "-r", "--raw_file",
            type=files.is_readable_file, metavar="FILE", required=True,
            help="Path to the binary file to be processed"
        )
        parser.add_argument(
            "-f", "--fps", type=int, required=True,
            help="Frames per second, required for timing calculation"
        )

        args = parser.parse_args(argv)
        return MLX90640RawDataProcessor(args.fps, args.raw_file)


if __name__ == "__main__":
    processor = MLX90640RawDataProcessor.create(sys.argv[1:])
