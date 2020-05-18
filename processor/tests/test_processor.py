import os, unittest

from processor import processor


class MLX90640Processor(unittest.TestCase):

    DATASET_DIR = 'datasets'
    DATASET_EXT = '.raw'

    def __init__(self, *args, **kwargs):
        super(MLX90640Processor, self).__init__(*args, **kwargs)

        self.datasets = [
            (int(f.split('-')[1]), int(f.split('-')[2]), os.path.join(MLX90640Processor.DATASET_DIR, f))
            for f in os.listdir(MLX90640Processor.DATASET_DIR)
            if os.path.isfile(os.path.join(MLX90640Processor.DATASET_DIR, f))
                and f.endswith(MLX90640Processor.DATASET_EXT)
        ]

    def test_process(self):

        print(f"datasets={self.datasets}")
        test_object = processor.MLX90640Processor(*self.datasets[0], plot_frames=False)
