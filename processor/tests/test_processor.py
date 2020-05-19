import unittest

from processor import dataset, processor


class MLX90640Processor(unittest.TestCase):

    DATASET_DIR = 'datasets'

    def setUp(self):
        self.dsmanager = dataset.DatasetsManager(self.DATASET_DIR)

    def test_reference_sample(self):
        test_dataset = 0
        test_object = processor.MLX90640Processor(
            *self.dsmanager.datasets[test_dataset],
            plot_frames=True, plot_general=True,
            jump_frames=self.dsmanager.datasets[test_dataset][0]
        )
