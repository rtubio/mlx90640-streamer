import os, unittest

from processor import processor


class TestMLX90640RawDataProcessor(unittest.TestCase):

    DATASET1_FILEPATH   = 'processor/tests/dataset/dataset-1-132K.bin'
    DATASET1_FPS        = 8

    DATASET2_FILEPATH   = 'processor/tests/dataset/dataset-2-200K.bin'
    DATASET2_FPS        = 8

    DATASET3_FILEPATH   = 'processor/tests/dataset/ds-4-tachiuo.raw'
    DATASET3_FPS        = 4

    def test_process(self):

        test_object = processor.MLX90640RawDataProcessor(
            self.DATASET3_FPS, '15', self.DATASET3_FILEPATH
        )
