"""This is the processor that digests the raw data from MLX90640 and analyzes it."""

import argparse
import matplotlib.pyplot as pl
import numpy as np

from xpython.common import files, logger


class MLX90640RawFrame(logger.LoggingClass):
    """RAW binary frame straight out from MLX90640
    This is an array of floats, with 32x24 elements (MLX90640 pixels)
    """

    def __init__(self, frame, time_us):
        """Default constructor
        frame - array with the pixel data
        time_us - timestamp (in microseconds) at which the image was taken
        """
        super(MLX90640RawFrame, self).__init__()

        self.frame       = frame
        self.time_us     = time_us

    def __str__(self):
        return "@" + str(self.time_us) + "[" + str(self.dim) + "]:" +\
            str([",".join(item) for item in self.frame.astype(str)])

    @property
    def dim(self):
        return self.frame.shape

    @property
    def size(self):
        return self.dim[0] * self.dim[1] * self.SIZE_PIXEL

    def process(self):
        """
        This method processes the given frame in order to analyze the thermal resistance of the image.
        """
        pass # self._l.debug(f"frame = {str(self)}")


class MLX90640RawDataProcessor(logger.LoggingClass):
    """RAW binary data file processor
    This class processes the raw binary data as gathered from MLX90640.
    Frames are suppossed to be stored sequentially within the file, at a rate of FPS
    frames per second. The value of FPS determines the time distance in between frames.
    """

    PIXELS_X        = 32
    PIXELS_Y        = 24
    PIXELS_FRAME    = PIXELS_X * PIXELS_Y
    SIZE_PIXEL      = np.dtype(np.float32).itemsize
    SIZE_FRAME      = PIXELS_FRAME * SIZE_PIXEL
    FRAME_SHAPE     = [PIXELS_X, PIXELS_Y]
    PX_DISTANCE_MM  = 10
    P0              = (int(PIXELS_X * 0.5), int(PIXELS_Y * 0.5))
    P1              = None
    P2              = None

    def __init__(self, fps, distance_mm, raw_filepath, px_distance_mm=10):
        """Default constructor
        fps - frames per second, necessary to calculate the timeline
        distance_mm - mm of distance from the camera to the target material
        raw_filepath - path to the binary file with the RAW frames
        px_distance_mm=10 - mm of distance from P0 to P1 or P2
        """
        super(MLX90640RawDataProcessor, self).__init__()

        self.fps = fps
        self.distance_mm = distance_mm
        self.raw_filepath = raw_filepath

        self._timestep_us = 1.0*1e6 / self.fps
        self.frames = []

        self.read()
        self.process()

    def read(self):
        """
        This method reads the frames from the given file, where the RAW data is supposed to be stored.
        """
        time_us = 0.0

        with open(self.raw_filepath, mode='rb') as f:
            while True:

                try:

                    array = np.fromfile(f, dtype=np.float32, count=self.PIXELS_FRAME)
                    self._l.debug(f"array[{len(array)}] = {array}")
                    frame = MLX90640RawFrame(array.reshape(self.FRAME_SHAPE), time_us)
                    self.frames.append(frame)
                    time_us += self._timestep_us

                except ValueError as ex:
                    print(f"[warn] Aborting file reading, reason = {ex}")
                    break

    def process(self):
        """
        This method processes the frames read from the file.
        """
        for f in self.frames:
            f.process()

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
