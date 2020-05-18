"""
@author rtpardavila[at]gmail[dot]com
"""

import os

from xpython.common import logger


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
            int(f.split('-')[1]),
            int(f.split('-')[2]),
            os.path.join(self.basedir, f)
        )
            for f in os.listdir(self.basedir)
                if os.path.isfile(os.path.join(self.basedir, f))
                    and f.endswith(DatasetsManager.DATASET_EXT)
        ]
