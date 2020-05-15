import os, unittest

from processor import processor


class MLX90640Processor(unittest.TestCase):

    datasets = [
        (15.0, 8, 'datasets/ds-1-132K.raw'),
        (15.0, 8, 'datasets/ds-2-200K.raw'),
        (15.0, 8, 'datasets/ds-3-150K-tachiuo.raw'),
        (15.0, 4, 'datasets/ds-4-tachiuo.raw'),
        (15.0, 4, 'datasets/ds-5-tachiuo.raw')
    ]

    def test_process(self):

        test_object = processor.MLX90640Processor(*self.datasets[4])
