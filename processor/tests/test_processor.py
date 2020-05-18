import unittest

from processor import dataset, processor


class MLX90640Processor(unittest.TestCase):

    DATASET_DIR = 'datasets'

    def setUp(self):
        self.dsmanager = dataset.DatasetsManager(self.DATASET_DIR)

    def test_process(self):

        test_object = processor.MLX90640Processor(
            *self.dsmanager.datasets[0],
            plot_frames=True
        )
