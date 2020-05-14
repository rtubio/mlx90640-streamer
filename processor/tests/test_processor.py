import os, unittest

from processor import processor


class TestMLX90640RawDataProcessor(unittest.TestCase):

    DATASET1_FILEPATH   = 'processor/tests/dataset/dataset-1-16K.bin'
    DATASET1_FPS        = 16

    DATASET2_FILEPATH   = 'processor/tests/dataset/dataset-2-2M3.bin'
    DATASET2_FPS        = 8

    def test_process(self):

        test_object = processor.MLX90640RawDataProcessor(
            self.DATASET2_FPS, self.DATASET2_FILEPATH
        )

        test_object.process()
