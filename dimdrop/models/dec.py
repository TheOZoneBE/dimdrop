from keras.optimizers import Adam
from keras.callbacks import EarlyStopping
from keras.models import Model
from sklearn.cluster import KMeans
import math

from .autoencoder import Autoencoder
from ..layers import ClusteringLayer
from ..util import DECSequence


class DEC(Autoencoder):
    def __init__(
            self,
            in_dim,
            out_dim,
            k,
            layer_sizes=[500, 500, 2000],
            epochs=1000,
            lr=0.1,
            scale=True,
            log=False,
            batch_size=256,
            patience=3,
            tol=0.01,
            verbose=0):
        super().__init__(in_dim, out_dim, layer_sizes=layer_sizes, lr=lr, scale=scale, log=log, batch_size=batch_size, patience=patience,
                         epochs=epochs, regularizer=None, pretrain_method='stacked', verbose=verbose)
        self.k = k
        self.tol = tol

    def fit(self, data):
        super().fit(data)
        data = self.data_transform(data)
        clustering_layer = ClusteringLayer(
            self.k, name='clustering')(self.encoder.output)

        if self.verbose:
            print('Initializing cluster centers')

        kmeans = KMeans(n_clusters=self.k, n_init=20)
        y_pred = kmeans.fit_predict(self.encoder.predict(data))
        self.clustering_model = Model(inputs=self.encoder.input,
                                      outputs=clustering_layer)

        self.clustering_model.get_layer(name='clustering').set_weights(
            [kmeans.cluster_centers_])

        self.clustering_model.compile(
            optimizer=Adam(self.lr, decay=self.lr / self.epochs),
            loss='kld'
        )
        sequence = DECSequence(data, self.clustering_model, self.batch_size)

        early_stopping = EarlyStopping(monitor='loss', patience=self.patience)
        if self.verbose:
            print('Clustering optimization')
        self.clustering_model.fit_generator(sequence, math.ceil(data.shape[0] / self.batch_size),  epochs=self.epochs, callbacks=[early_stopping],
                                            verbose=self.verbose)
