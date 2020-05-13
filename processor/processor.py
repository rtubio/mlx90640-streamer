"""
This is the processor that digests the raw data from MLX90640 and analyzes it.
"""

import argparse

from xpython.common import logger


class MLX90640RawFrame(logger.LoggingClass):
    """RAW binary frame straight out from MLX90640
    This is an array of type uint16_t, with a fixed length of 834 elements
    """

    LENGTH = 834

    def __init__(self, fps, file_path):
        """Default constructor
        fps - frames per second, necessary to calculate the timeline
        file_path - path to the binary file with the RAW frames
        """
        self.fps = fps
        self.file_path = file_path


class MLX90640RawFrameProcessor(logger.LoggingClass):

    @staticmethod
    def create(argv):
        # Basic class static factory method.

        parser = argparse.ArgumentParser(description="Updates old JSON file with new JSON file")
        parser.add_argument(
            "-o", "--old",
            type=files.is_writable_file, metavar="FILE", required=True,
            help="Path to the old JSON file to be updated"
        )
        parser.add_argument(
            "-n", "--new",
            type=files.is_writable_file, metavar="FILE", required=True,
            help="Path to the new JSON file to use to update the old one"
        )
        parser.add_argument(
            "-b", "--backup",
            default=False, action="store_true", required=False,
            help="Enables creating a backup of the old file"
        )
        args = parser.parse_args(argv)
        return MLX90640RawFrameProcessor(args.old, args.new, backup=args.backup)


if __name__ == "__main__":
    print(f"Test, {__name__}")
