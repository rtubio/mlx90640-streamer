"""
@author rtpardavila[at]gmail[dot]com
"""

import argparse, os, sys

import processor
from xpython.common import logger, files


class DatasetsManager(logger.LoggingClass):
    """
    This class facilitates the reading of the available datasets under a given directory.
    """

    DATASET_EXT = '.raw'

    def __init__(self, basedir):
        """Default constructor
        Reads all the dataset available files directly under the given directory. It assumes that those
        files meet the following naming convention:

                ds-$FPS-$DMM-$DATE-$SEQ-$DESCRIPTION.raw

        The filename is decomposed using split assuming that '-' is always used as a separator among those
        fields. The definition of those fields is as follows:

            a) $FPS ~ integer with the frames per second (1, 2, 4, 8, 16), following the restrictions from
                        the MLX90640 device
            b) $DMM ~ acronym for distance in mm and represents the distance from the camera to the surface
                        of the object in test
            c) $DATE ~ the date when the experiment was carried out, REQUIRED but not USED
            d) $SEQ ~ sequential number of the experiment, REQUIRED but not USED
            e) $DESCRIPTION ~ human readable brief descripiton to easily identify the experiment

        The arguments for this constructor are the following ones:

            basedir - path to the base directory under which the dataset files are kept.
        """
        super(DatasetsManager, self).__init__()

        self.basedir = basedir

        self.datasets = [(
            1, # int(f.split('-')[1]), # Due to an issue with the driver, all datasets are FPS=1
            int(f.split('-')[2]),
            os.path.join(self.basedir, f)
        )
            for f in sorted(os.listdir(self.basedir))
                if os.path.isfile(os.path.join(self.basedir, f))
                    and f.endswith(DatasetsManager.DATASET_EXT)
        ]

    def __str__(self):
        return "\n\t".join(["FPS = {:2}, file = {}".format(ds[0], ds[2]) for ds in self.datasets])

    def list(self):
        self._l.info(f"datasets = \n\t{str(self)}")

    def analyze(self, index, update=False):
        ds = self.datasets[index]
        processor.MLX90640Processor(*ds, update=update)

    def analyze_all(self, update=False):
        for ds_index in range(len(self.datasets)):
            try:
                self.analyze(ds_index, update=update)
            except Exception as ex:
                self._l.error(f"Exception while processing dataset {self.datasets[ds_index]}, msg = {ex}")

    @staticmethod
    def create(argv):
        """Factory method to instantiate the class using the arguments from the CLI"""

        parser = argparse.ArgumentParser(description="Manages the datasets for the thermalbench/MLX90640")
        parser.add_argument(
            "-l", "--list",
            action='store_true', required=False,
            help="Lists the available dataset files"
        )
        parser.add_argument(
            "-u", "--update",
            action='store_true', required=False,
            help="This flag forces the processor to update the results for all existing datasets"
        )
        parser.add_argument(
            "-d", "--directory",
            type=files.is_writable_dir, metavar="FILE", default=os.getcwd(),
            help="Directory with the datasets"
        )
        parser.add_argument(
            "-a", "--analyze",
            type=int, required=False,
            help="Analyzes the dataset whose index is given as a parameter of the call"
        )

        args = parser.parse_args(argv)

        if 'list' in args and args.list:
            DatasetsManager(args.directory).list()
        if 'analyze' in args and args.analyze:
            index = args.analyze
            if (index == -1):
                DatasetsManager(args.directory).analyze_all(update=args.update)
            else:
                DatasetsManager(args.directory).analyze(args.analyze, update=args.update)


if __name__ == "__main__":
    processor = DatasetsManager.create(sys.argv[1:])
