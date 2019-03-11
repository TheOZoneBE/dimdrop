import numpy as np


class Transform:
    def __init__(self, scale=True, log=False):
        self.scale = scale
        self.log = log

    def __call__(self, data):
        if not self.scale and not self.log:
            return data
        if self.log:
            output = np.log2(data + 1)
        if self.scale:
            output = np.zeros(data.shape, dtype=np.float32)
            for i in range(data.shape[0]):
                output[i, :] = data[i, :] / np.max(data[i, :])
        return output
