from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import tensorflow as tf
import numpy as np

CONFIGURATIONS = {'tf_gpu_options': tf.GPUOptions(allow_growth=True), # MTCNN Face align config
    'align_minsize': 30,  # minimum size of face
    'align_threshold': [0.6, 0.7, 0.7],  # three steps's threshold
    'align_factor': 0.709  # scale factor
    }
