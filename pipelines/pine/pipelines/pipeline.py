# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import abc
import typing

class NerPrediction(object):
    def __init__(self, offset_start: int, offset_end: int, label: str):
        self.offset_start: int = offset_start
        self.offset_end: int = offset_end
        self.label: str = label

    def serialize(self) -> typing.Tuple[int, int, str]:
        return (self.offset_start, self.offset_end, self.label)

class DocumentPredictions(object):
    def __init__(self, ner: typing.List[NerPrediction], doc: typing.List[str], extra_data: typing.Any = None):
        self.ner = ner
        self.doc = doc
        self.extra_data = extra_data

    def serialize(self) -> dict:
        return {
            "ner": [n.serialize() for n in self.ner],
            "doc": self.doc
        }

class NerPredictionProbabilities(object):
    def __init__(self, offset_start: int, offset_end: int, predictions: typing.List[typing.Tuple[str, float]]):
        self.offset_start = offset_start
        self.offset_end = offset_end
        self.predictions = predictions

    def get_highest_prediction(self) -> typing.Tuple[str, float]:
        return max(self.predictions, key=lambda t: t[1])

    def get_predictions_from_highest_to_lowest(self) -> typing.List[typing.Tuple[str, float]]:
        return sorted(self.predictions, key=lambda t: t[1], reverse=True)

    def serialize(self) -> typing.Tuple[int, int, typing.List[typing.Tuple[str, float]]]:
        return (self.offset_start, self.offset_end, self.predictions)

class DocumentPredictionProbabilities(object):
    def __init__(self, ner: typing.List[NerPredictionProbabilities], doc: typing.List[typing.Tuple[str, float]]):
        self.ner = ner
        self.doc = doc

    def serialize(self) -> dict:
        return {
            "ner": [n.serialize() for n in self.ner],
            "doc": self.doc
        }

class Pipeline(object, metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def __init__(self):
        raise NotImplementedError('Must define __init__ to use Pipeline Base Class')

    # status()
    @abc.abstractmethod
    def status(self) -> dict:
        raise NotImplementedError('Must define status to use Pipeline Base Class')

    # fit(X, y)
    # internal state is changed
    @abc.abstractmethod
    def fit(self, X, y, **params) -> dict:
        raise NotImplementedError('Must define fit to use Pipeline Base Class')

    # predict(X)
    # returns [[[offset_start, offset_end, label], ..., ...]
    @abc.abstractmethod
    def predict(self, X: typing.Iterable[str]) -> typing.List[DocumentPredictions]:
        raise NotImplementedError('Must define predict to use Pipeline Base Class')

    # predict_proba(X)
    # returns [[[offset_start, offset_end, label, score], ...], ...]
    # can also return scores for all labels if get_all is True
    @abc.abstractmethod
    def predict_proba(self, X: typing.Iterable[str], **kwargs) -> typing.List[DocumentPredictionProbabilities]:
        raise NotImplementedError('Must define predict_proba to use Pipeline Base Class')

    # next_example(X, Xid)
    # Given model's current state evaluate the input (id, String) pairs and return a rank ordering of lowest->highest scores for instances (will need to discuss specifics of ranking)
    # Discussing rank is now a major project - see notes
    @abc.abstractmethod
    def next_example(self, X, Xid):
        raise NotImplementedError('Must define next_example to use Pipeline Base Class')

    # saves model so that it can be loaded again later
    @abc.abstractmethod
    def save_model(self, model_name):
        raise NotImplementedError('Must define save_model to use Pipeline Base Class')

    # loads a previously saved model
    @abc.abstractmethod
    def load_model(self, model_name):
        raise NotImplementedError('Must define load_model to use Pipeline Base Class')
