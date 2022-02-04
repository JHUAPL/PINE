# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import importlib
import logging
import os
import typing

from .pipeline import Pipeline, DocumentPredictions, DocumentPredictionProbabilities, EvaluationMetrics

from overrides import overrides

logger = logging.getLogger(__name__)

#ASSUMED INPUTS
#X = [string]
#y = [[(start offset, stop offset, label), ()], ... []]
#Xid = [id]

class NER(Pipeline):
    __lib = ''
    pipeline = -1

    __SUPPORTED_PIPELINES = ['spacy', 'corenlp', 'opennlp', 'simpletransformers']    

    #initializes proper nlp library pipeline based on user selection
    #there are additional args to accomodate initializing different pipelines, check individual pipeline for specifics
    def pipe_init(self, x, **kwargs):
        parent_mod = ".".join(NER.__module__.split(".")[:-1])
        if x in self.__SUPPORTED_PIPELINES:
            module = importlib.import_module(parent_mod+'.'+x+'_NER_pipeline')
            targetClass = getattr(module, x+'_NER')
            return targetClass(**kwargs)
        else: 
            return -1

    #init()
    #set tunable parameters
    #if an invalid pipeline is specified it defaults to spacy
    def __init__(self, lib=None, **kwargs):
        self.__lib = lib
        logger.info('initializing library')
        self.pipeline = self.pipe_init(self.__lib, **kwargs)
        if (self.pipeline == -1):
            logger.warning('WARNING: Invalid pipeline \'', self.__lib, '\' specified, currently only ', self.__SUPPORTED_PIPELINES,' are allowed. Defaulting to spacy')
            self.pipeline = self.pipe_init('spacy', **kwargs)
            self.__lib = 'spacy'

    @property
    def pipeline_class(self):
        return self.pipeline.__class__.__module__ + "." + self.pipeline.__class__.__name__

    @overrides
    def status(self) -> dict:
        return self.pipeline.status()

    #internal state is changed
    #kwargs varies between pipelines, see individual pipeline for extra arguments
    @overrides
    def fit(self, X: typing.Iterable[str], y, all_labels: typing.Iterable[str], **params) -> dict:
        return self.pipeline.fit(X, y, all_labels, **params)

    @overrides
    def predict(self, X: typing.Iterable[str]) -> typing.List[DocumentPredictions]:
        return self.pipeline.predict(X)

    #kwargs varies between pipelines, see individual pipeline for extra arguments
    @overrides
    def predict_proba(self, X: typing.Iterable[str], **kwargs) -> typing.List[DocumentPredictionProbabilities]:
        return self.pipeline.predict_proba(X, **kwargs)

    @overrides
    def evaluate(self, X: typing.Iterable[str], y, all_labels: typing.Iterable[str], **kwargs) -> EvaluationMetrics:
        return self.pipeline.evaluate(X, y, all_labels, **kwargs)

    #next_example(Xid)
    #Given model's current state evaluate the input (id, String) pairs and return a rank ordering of lowest->highest scores for instances (will need to discuss specifics of ranking)
    @overrides
    def next_example(self, X: typing.Iterable[str], Xid):
        #may want to program it here instead of one level down, as the ranking function might not change with the pipeline used
        return self.pipeline.next_example(X, Xid)

    @overrides
    def save_model(self, model_name: str):
        directory = os.path.dirname(model_name)
        # if directories in path dont exists create them
        if not os.path.exists(directory):
            os.makedirs(directory)

        return self.pipeline.save_model(model_name)

    @overrides
    def load_model(self, model_name: str):
        self.pipeline.load_model(model_name)
