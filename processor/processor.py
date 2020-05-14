"""This is the processor that digests the raw data from MLX90640 and analyzes it."""

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
    SIZE_PIXEL      = np.dtype(np.float32).itemsize
    SIZE_FRAME      = PIXELS_FRAME * SIZE_PIXEL

    def __init__(self, frame, time_us):
        """Default constructor
        data - array with the pixel data
        """
        super(MLX90640RawFrame, self).__init__()
        self.frame      = frame
        self.time_us    = time_us

        self._l.debug(f"{str(self.frame)}")

    def __str__(self):
        return "frame@" + str(self.time_us) + ":" + str([",".join(item) for item in self.frame.astype(str)])

    @property
    def dim(self):
        return self.frame.shape

    @property
    def size(self):
        return self.dim[0] * self.dim[1] * self.SIZE_PIXEL

    @staticmethod
    def read(file, time_us):
        """
        This method creates a frame by reading its data from the given file.
        file - file object to read binary data from.
        """
        array = np.fromfile(file, dtype=np.float, count=MLX90640RawFrame.PIXELS_FRAME)
        return MLX90640RawFrame(
            array.reshape([MLX90640RawFrame.PIXELS_X, MLX90640RawFrame.PIXELS_Y]),
            time_us
        )


class MLX90640RawDataProcessor(logger.LoggingClass):
    """RAW binary data file processor
    This class processes the raw binary data as gathered from MLX90640.
    Frames are suppossed to be stored sequentially within the file, at a rate of FPS
    frames per second. The value of FPS determines the time distance in between frames.
    """

    # datatype = np.dtype([(np.float, MLX90640RawFrame.PIXELS_X * MLX90640RawFrame.PIXELS_Y)])
    datatype = np.dtype(np.float32)

    def __init__(self, fps, raw_filepath):
        """Default constructor
        fps - frames per second, necessary to calculate the timeline
        raw_filepath - path to the binary file with the RAW frames
        """
        self.fps = fps
        self.raw_filepath = raw_filepath
        self._timestep_us = 1.0*1e6 / self.fps
        self.frames = {}

    def process(self):
        """
        This method processes the given file, where the RAW data is supposed to be stored.
        """
        t_us = 0.0

        with open(self.raw_filepath, mode='r') as f:
            while True:

                try:

                    frame = MLX90640RawFrame.read(f, t_us)
                    print(f"@{t_us}, len = {frame.dim}, size = {frame.size}")
                    self.frames[t_us] = frame
                    t_us += self._timestep_us

                except ValueError as ex:
                    print(f"[warn] Aborting file reading, reason = {ex}")
                    break

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
