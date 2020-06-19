# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import importlib
import logging
import os

from .pipeline import Pipeline

logger = logging.getLogger(__name__)

#ASSUMED INPUTS
#X = [string]
#y = [[(start offset, stop offset, label), ()], ... []]
#Xid = [id]

class NER(Pipeline):
    __lib = ''
    pipeline = -1

    __SUPPORTED_PIPELINES = ['spacy', 'corenlp', 'opennlp']    

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

        
    #fit(X, y)
    #returns nothing
    #internal state is changed
    #kwargs varies between pipelines, see individual pipeline for extra arguments
    def fit(self, X, y, kwargs):
        return self.pipeline.fit(X, y, kwargs)

    #predict(X)
    #returns {doc_id:[(offset_start, offset_end, label), ... ()]}
    def predict(self, X, Xid):
        return self.pipeline.predict(X, Xid)

    #predict_proba(X)
    #returns {doc_id:[(offset_start, offset_end, label, confidence), ... ()]}
    #kwargs varies between pipelines, see individual pipeline for extra arguments
    def predict_proba(self, X, Xid, **kwargs):
        return self.pipeline.predict_proba(X, Xid, **kwargs)

    # evaluate(X, y, Xid)
    # returns stats
    def evaluate(self, X, y, Xid, **kwargs):
        return self.pipeline.evaluate(X, y, Xid, **kwargs)

    #next_example(Xid)
    #Given model's current state evaluate the input (id, String) pairs and return a rank ordering of lowest->highest scores for instances (will need to discuss specifics of ranking)
    def next_example(self, X, Xid):
        #may want to program it here instead of one level down, as the ranking function might not change with the pipeline used
        return self.pipeline.next_example(X, Xid)

    #saves model so that it can be loaded again later
    #models must be saved with extension ".ser.gz"
    # save_model(path)
    def save_model(self, model_path):
        directory = os.path.dirname(model_path)
        # if directories in path dont exists create them
        if not os.path.exists(directory):
            os.makedirs(directory)

        return self.pipeline.save_model(model_path)

    #loads a previously saved model
    #properties can be exported/imported during train
    def load_model(self, model_name):
        self.pipeline.load_model(model_name)
