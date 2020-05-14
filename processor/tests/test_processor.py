import os, unittest

from processor import processor


class TestMLX90640RawDataProcessor(unittest.TestCase):

    DATASET1_FILEPATH   = 'processor/tests/dataset/dataset-1-16k.bin'
    DATASET1_FPS        = 16

    def test_process(self):

        test_object = processor.MLX90640RawDataProcessor(
            self.DATASET1_FPS, self.DATASET1_FILEPATH
        )

        test_object.process()
