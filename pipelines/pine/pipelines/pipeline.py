# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import abc

class Pipeline(object, metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def __init__(self):
         raise NotImplementedError('Must define __init__ to use Pipeline Base Class')

    @abc.abstractmethod
    def fit(self, X, y):
         raise NotImplementedError('Must define fit to use Pipeline Base Class')

    @abc.abstractmethod
    def predict(self, X, Xid):
         raise NotImplementedError('Must define predict to use Pipeline Base Class')

    @abc.abstractmethod
    def predict_proba(self, X, Xid):
         raise NotImplementedError('Must define predict_proba to use Pipeline Base Class')

    @abc.abstractmethod
    def next_example(self, X, Xid):
         raise NotImplementedError('Must define next_example to use Pipeline Base Class')

    @abc.abstractmethod
    def save_model(self, model_name):
        raise NotImplementedError('Must define save_model to use Pipeline Base Class')

    @abc.abstractmethod
    def load_model(self, model_name):
        raise NotImplementedError('Must define load_model to use Pipeline Base Class')
