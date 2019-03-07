from keras.callbacks import Callback
import numpy as np
from keras import backend as K

import random


class KMeansRegularizer(Callback):
    """
    Custom keras regularizer to apply k-means loss to a network

    Parameters
    ----------
    cluster_centers : array
        The initial cluster centers
    batch_size : int, optional
        The batch size of the network
    weight : float
        The strength of the regularizer
    """
    __name__ = 'kmeans_regularizer'

    def __init__(self, cluster_centers, batch_size=100, weight=0.5):
        self.cluster_centers = cluster_centers
        self.batch_size = batch_size
        self.weight = K.variable(weight)

    def init_fit(self, encoder, input_data):
        """
        Initialize this regularizer for a fitting operation

        Parameters
        ----------
        encoder : keras model
            The encoder part of the model being fitted
        input_data : array
            The fitting data
        """
        self.encoder = encoder
        self.input_data = input_data

    def on_epoch_end(self, epoch, logs=None):
        """
        Executed at the end of every epoch. Recalculates the cluster centers.

        Parameters
        ----------
        epoch : int
            The current epoch
        logs : dictionary
            The logs of the model
        """
        # update cluster centers
        encoding = self.encoder.predict(self.input_data)
        new_centers = np.zeros(self.cluster_centers.shape)
        counters = np.zeros(self.cluster_centers.shape[0])
        for point in encoding:
            dist_2 = np.sum((self.cluster_centers - point)**2, axis=1)
            min_dist = np.argmin(dist_2)
            new_centers[min_dist] += point
            counters[min_dist] += 1

        self.cluster_centers = np.array(
            [new_centers[i] / counters[i] for i in range(len(counters))])
        self.__fix_centers()

    def __call__(self, activations):
        dists = K.map_fn(self.__cluster_dist, activations)

        squared = K.square(dists)
        return self.weight * K.sum(squared)

    def __fix_centers(self):
        false_centers = [i for i in range(
            len(self.cluster_centers)) if np.isnan(self.cluster_centers[i][0])]
        true_centers = [i for i in range(
            len(self.cluster_centers)) if not np.isnan(self.cluster_centers[i][0])]
        for index in false_centers:
            sample = random.sample(true_centers, 3)
            new_center = np.zeros(2)
            for el in sample:
                new_center += self.cluster_centers[el]

            self.cluster_centers[index] = new_center / 3

    def __cluster_dist(self, activation):
        dist_2 = K.sum((self.cluster_centers - activation)**2, axis=1)
        min_dist = np.argmin(dist_2)

        return dist_2[min_dist]
