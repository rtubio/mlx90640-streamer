"""This is the processor that digests the raw data from MLX90640 and analyzes it."""

import argparse
import matplotlib.pyplot as pl
import numpy as np
import os
import pathlib
import shutil

from xpython.common import files, logger


class MLX90640Frame(logger.LoggingClass):
    """RAW binary frame straight out from MLX90640
    This is an array of floats, with 32x24 elements (MLX90640 pixels)
    """

    def __init__(self, frame, time_us):
        """Default constructor
        frame - array with the pixel data
        time_us - timestamp (in microseconds) at which the image was taken
        """
        super(MLX90640Frame, self).__init__()

        self.frame = frame
        self.time_us = time_us
        self.image_filename = "-".join([MLX90640Processor.dataset_name, "{:.0f}".format(self.time_us)]) + '.png'
        self.image_filepath = os.path.join(MLX90640Processor.dataset_dirpath, self.image_filename)

        self._l.debug(f"{self.image_filepath}")

    def __str__(self):
        return "@" + str(self.time_us) + "[" + str(self.dim) + "]:" +\
            str([",".join(item) for item in self.frame.astype(str)])

    @property
    def dim(self):
        return self.frame.shape

    @property
    def size(self):
        return self.dim[0] * self.dim[1] * self.SIZE_PIXEL

    def pixel(self, coordinates):
        return self.frame[coordinates[0], coordinates[1]]

    def _annotateTemperature(self, coordinates, temperature, fontsize=6, shift_x=2, shift_y=0):
        pl.text(
            coordinates[0]+shift_x, coordinates[1]+shift_y, f"{temperature:.1f}",
            horizontalalignment='right', verticalalignment='center', fontsize=fontsize
        )
        pl.plot(*coordinates, 'X')

    def plot(self):

        fig, ax = pl.subplots()
        fig.suptitle(f"{MLX90640Processor.dataset_name} :: {self.time_us:.0f} (us) :: {self.diff_t_12:.3f} (degC)")
        image = pl.imshow(
            self.frame, aspect='auto', cmap=pl.get_cmap('jet'),
            vmin=MLX90640Processor.T_MIN_C, vmax=MLX90640Processor.T_MAX_C
        )
        fig.colorbar(image)

        self._annotateTemperature(MLX90640Processor.REF_PIXEL_0, self.ref_t_0)
        self._annotateTemperature(MLX90640Processor.REF_PIXEL_1, self.ref_t_1)
        self._annotateTemperature(MLX90640Processor.REF_PIXEL_2, self.ref_t_2)

        pl.savefig(self.image_filepath, dpi=300)
        pl.close()

    def process(self):
        """
        This method processes the given frame in order to analyze the thermal resistance of the image.
        """
        self._l.debug(f"> Processing: {MLX90640Processor.dataset_name}@{self.time_us:.0f}")

        self.ref_t_0 = self.pixel(MLX90640Processor.REF_PIXEL_0)
        self.ref_t_1 = self.pixel(MLX90640Processor.REF_PIXEL_1)
        self.ref_t_2 = self.pixel(MLX90640Processor.REF_PIXEL_2)

        self.diff_t_12 = np.abs(self.ref_t_1 - self.ref_t_2)

        """
        self._l.debug(f"@{self.time_us:.0f}: t0 (@{MLX90640Processor.REF_PIXEL_0}) > {self.ref_t_0:.1f}")
        self._l.debug(f"@{self.time_us:.0f}: t1 (@{MLX90640Processor.REF_PIXEL_1}) > {self.ref_t_1:.1f}")
        self._l.debug(f"@{self.time_us:.0f}: t2 (@{MLX90640Processor.REF_PIXEL_2}) > {self.ref_t_2:.1f}")
        self._l.debug(f"@{self.time_us:.0f}: t12 > {self.diff_t_12:.1f}")
        """

        self.plot()

        return (self.ref_t_0, self.ref_t_1, self.ref_t_2, self.diff_t_12)


class MLX90640Processor(logger.LoggingClass):
    """RAW binary data file processor
    This class processes the raw binary data as gathered from MLX90640.
    Frames are suppossed to be stored sequentially within the file, at a rate of FPS
    frames per second. The value of FPS determines the time distance in between frames.
    """

    PIXELS_X        = 32
    PIXELS_Y        = 24
    PIXELS_FRAME    = PIXELS_X * PIXELS_Y
    FOV_X_DEG       = 110.
    FOV_Y_DEG       = 75.
    SENSOR_XSIDE_MM = 2
    PIXEL_XSIDE_UM  = int((1e3 * SENSOR_XSIDE_MM) / PIXELS_X)
    SENSOR_YSIDE_MM = 3
    PIXEL_YSIDE_UM  = int((1e3 * SENSOR_YSIDE_MM) / PIXELS_Y)
    SIZE_PIXEL      = np.dtype(np.float32).itemsize
    SIZE_FRAME      = PIXELS_FRAME * SIZE_PIXEL
    FRAME_SHAPE     = [PIXELS_X, PIXELS_Y]

    T_MAX_C         = +80
    T_MIN_C         = -15
    T_RANGE         = T_MAX_C - T_MIN_C

    def calculate_reference_pixels(self):
        """
        This function calculates the position within the matrix of the pixels to be used as a reference
        for the calculation of the thermal resistance. It uses the given target physical distance, and
        it calculates which pixels correspond to that distance.
        """

        self.gsd_mm = (
            0.5*self.PIXEL_XSIDE_UM/1e3 + self.distance_mm*np.tan(self.FOV_X_DEG),
            0.5*self.PIXEL_YSIDE_UM/1e3 + self.distance_mm*np.tan(self.FOV_Y_DEG)
        )
        self.ref_pixels_distance = (
            int(self.distance_mm / self.gsd_mm[0]),
            int(self.distance_mm / self.gsd_mm[1])
        )

        MLX90640Processor.REF_PIXEL_0 = (
            int(self.PIXELS_X * 0.5),
            int(self.PIXELS_Y * 0.5)
        )
        MLX90640Processor.REF_PIXEL_1 = (
            int(self.PIXELS_X * 0.5),
            int(self.PIXELS_Y * 0.5) + self.ref_pixels_distance[1]
        )
        MLX90640Processor.REF_PIXEL_2 = (
            int(self.PIXELS_X * 0.5),
            int(self.PIXELS_Y * 0.5) - self.ref_pixels_distance[1]
        )

        self._l.debug(f"> r_pix_0 = ({self.REF_PIXEL_0})")
        self._l.debug(f"> r_pix_1 = ({self.REF_PIXEL_1})")
        self._l.debug(f"> r_pix_2 = ({self.REF_PIXEL_2})")

    def __init__(self, fps, distance_mm, raw_filepath, px_distance_mm=10):
        """Default constructor
        fps - frames per second, necessary to calculate the timeline
        distance_mm - mm of distance from the camera to the target material
        raw_filepath - path to the binary file with the RAW frames
        px_distance_mm=10 - mm of distance from P0 to P1 or P2
        """
        super(MLX90640Processor, self).__init__()

        self.fps = fps
        self.distance_mm = distance_mm
        self.raw_filepath = raw_filepath
        self.px_distance_mm = px_distance_mm

        self.timestep_us = 1e6 / self.fps
        self.frames = []

        MLX90640Processor.dataset_name = pathlib.Path(self.raw_filepath).stem
        MLX90640Processor.dataset_dirpath = os.path.join(
            os.path.dirname(os.path.abspath(self.raw_filepath)), self.dataset_name
        )

        if os.path.isdir(self.dataset_dirpath) and os.path.exists(self.dataset_dirpath):
            shutil.rmtree(self.dataset_dirpath, ignore_errors=True)
        os.mkdir(self.dataset_dirpath)

        self.calculate_reference_pixels()
        self.read()
        self.process()

    def read(self):
        """
        This method reads the frames from the given file, where the RAW data is supposed to be stored.
            > The image frames are to be stored as a sequence of float32 numbers, in binary format.
            > The data is to be stored as 24 arrays of 32 consecutive float32 numbers.
        """
        time_us = 0.0

        with open(self.raw_filepath, mode='rb') as f:
            while True:

                try:

                    array = np.fromfile(f, dtype=np.float32, count=self.PIXELS_FRAME)
                    frame = MLX90640Frame(array.reshape(self.FRAME_SHAPE), time_us)
                    self.frames.append(frame)
                    time_us += self.timestep_us

                except ValueError as ex:
                    print(f"[warn] Aborting file reading, reason = {ex}")
                    break

    def process(self):
        self.results = [f.process() for f in self.frames]

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
        return MLX90640Processor(args.fps, args.raw_file)


if __name__ == "__main__":
    processor = MLX90640Processor.create(sys.argv[1:])
