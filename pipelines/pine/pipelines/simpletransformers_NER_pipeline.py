#!/usr/bin/env python3
# coding: utf8
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging
import os
import os.path
from shutil import copyfile
import uuid

import typing

from overrides import overrides

from .pipeline import Pipeline, NerPrediction, DocumentPredictions, NerPrediction, NerPredictionProbabilities, DocumentPredictionProbabilities, EvaluationMetrics, StatMetrics
from .shared.config import ConfigBuilder

from nltk.tokenize import WhitespaceTokenizer
from nltk.tokenize.punkt import PunktSentenceTokenizer
import numpy as np
import pandas as pd
from simpletransformers.ner import NERModel, NERArgs

config = ConfigBuilder.get_config()
logger = logging.getLogger(__name__)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)

# TODO: Change the collections.json file to default the collection for simple transformers with real classifiers, etc

class simpletransformers_NER(Pipeline):
    
    def __init__(self, tmp_dir=None):
        self.__id = uuid.uuid4()
        if tmp_dir != None:
            self.__temp_dir = tmp_dir
            #can choose to dictate where the model will store files so that it doesn't overwrite any, 
            #otherwise it will write to a new directory within the resources folder
        else:
            self.__temp_dir = config.ROOT_DIR + '/tmp/simpletransformers-' + str(self.__id)
        
        self.__model_dir = os.path.join(self.__temp_dir, "OUTPUT_MODEL/")
        self.__default_model_args = {
            # TODO: Some of these should be args passed in with defaults, probably epoch size, the dirs, any others Brant might say
            # TODO: There is a runs/ directory that is default created in the current directory where this is ran (pipelines/),
            # there might be an option to change that, or maybe just add to gitignore?
            "output_dir": self.__model_dir,
            "cache_dir": os.path.join(self.__temp_dir, "CACHE_DIR/"),
            "tensorboard_dir": os.path.join(self.__temp_dir, "TENSORBOARD/"),
            "max_seq_length": 128,
            "train_batch_size": 16,
            "gradient_accumulation_steps": 1,
            "eval_batch_size": 8,
            "num_train_epochs": 1,
            "weight_decay": 0,
            "learning_rate": 4e-5,
            "adam_epsilon": 1e-8,
            "warmup_ratio": 0.06,
            "warmup_steps": 20,
            "max_grad_norm": 1.0,

            "logging_steps": 50,
            "save_steps": 500,

            "overwrite_output_dir": True,
            "reprocess_input_data": False,
            "evaluate_during_training": False,
        }
        # TODO: Switch back to bioclinical bert, and also adding this as an option to change.
        # All models we can use: https://huggingface.co/models
        # self.__model_name = "emilyalsentzer/Bio_ClinicalBERT"
        # This currently being used because it is faster.
        self.__model_type = "bert"
        self.__model_name = "google/mobilebert-uncased"
        self.__model_use_cuda = False
        self.__model = None
        self.__sentence_tokenizer = PunktSentenceTokenizer()
        self.__word_tokenizer = WhitespaceTokenizer()

    # status()
    @overrides
    def status(self) -> dict:
        return {
            "default_model_args": self.__default_model_args
        }

    # fit(X, y)
    # internal state is changed
    @overrides
    def fit(self, X: typing.Iterable[str], y, all_labels: typing.Iterable[str], **params) -> dict:
        # setting up params
        model_args = self.__default_model_args.copy()
        if params is not None:
            for key in model_args.keys():
                if key in params:
                    model_args[key]= params[key]
        logger.info("Training with parameters: {}".format(model_args))
        
        # First, need to set up the data into a pandas dataframe and format our labels
        df = self._format_data(X, y)
        labels = self._format_labels(all_labels)
        
        # Create a new model, needs to be here for now since this is where we get labels
        if not self.__model:
            self.__model = NERModel(self.__model_type, self.__model_name, labels=labels,
                     use_cuda=self.__model_use_cuda, args=model_args)

        # After this, the model should be trained, and output files created
        self.__model.train_model(df, verbose=False, silent=True,
                                 show_running_loss=False)

        return {}

    @overrides
    def evaluate(self, X: typing.Iterable[str], y, all_labels: typing.Iterable[str], **kwargs) -> EvaluationMetrics:
        if not self.__model:
            raise Exception("Can't evaluate until model has been trained or loaded")
        
        # First, need to set up the data into a pandas dataframe and format our labels
        df = self._format_data(X, y)
        
        # No need to recreate model, as this is only run after fit().
        
        # Evaluate.
        result, model_outputs, preds_list = self.__model.eval_model(
            df, verbose=False)
        # acc=sklearn.metrics.accuracy_score
        logger.info("Evaluated model, result={}".format(result))
        
        metrics = EvaluationMetrics()
        metrics.totals.precision = result["precision"]
        metrics.totals.recall = result["recall"]
        metrics.totals.f1 = result["f1_score"]
        
        # TODO: need acc
        # TODO: need metrics for each label
        
        return metrics

    # predict(X)
    @overrides
    def predict(self, X: typing.Iterable[str]) -> typing.List[DocumentPredictions]:
        # First, make sure this model has been trained
        if not self.__model:
            return None

        # Make predictions with the model
        return_preds = []
        for doc in X:
            data = [s for s in self._sentencize(doc)]
            predictions, _ = self.__model.predict([sentence for (_, _, sentence) in data])
            return_preds.append(self._format_prediction(data, predictions))

        return return_preds

    # predict_proba(X)
    # can also return scores for all labels if get_all is True
    @overrides
    def predict_proba(self, X: typing.Iterable[str], **kwargs) -> typing.List[DocumentPredictionProbabilities]:
        # TODO: Need to implement this.
        # The "raw_outputs" (second item in tuple returned from predict) is probably useful for this.
        # Can turn predictions into probabilities for each label by running:
        # Where the array passed in refers to each word (print raw_outputs in the expanded_ner.py file to see this)
        # a = np.asarray([-0.2597193, 0.3929489, 0.42044127, 0.65579444, -0.075302914, 0.0072728638, 0.11236907, -0.035289638, -0.09346388, -0.25901815, -0.16599336, -0.06283752, -0.2664347])
        # prob = softmax(a)
        # prob is then equal to: array([0.0552652 , 0.10614558, 0.10910426, 0.13805568, 0.06645731,
        # 0.07217802, 0.0801766 , 0.0691704 , 0.06526127, 0.05530396,
        # 0.06069549, 0.06729091, 0.05489531]) which look like the probabilities of the labels (there are the same number of elements as labels)
        # It probably refers to the order of the labels given in, so if the labels arg was ['B-geo', 'I-geo'...] then 
        # B-geo is probably 0.0552652 and I-geo is probably 0.10614558... etc
        return []

    # next_example(X, Xid)
    # Given model's current state evaluate the input (id, String) pairs and return a rank ordering of lowest->highest scores for instances (will need to discuss specifics of ranking)
    # Discussing rank is now a major project - see notes
    @overrides
    def next_example(self, X: typing.Iterable[str], Xid):
        # Don't think we needed to do anything with this.
        return None

    # saves model so that it can be loaded again later
    @overrides
    def save_model(self, model_name: str):
        # Save all files from the output dir to the desired spot in order to load
        os.mkdir(model_name)
        # Copy from the tmp directory - but not the checkpoints
        for filename in os.listdir(self.__model_dir):
            if "checkpoint" not in filename:
                copyfile(os.path.join(self.__model_dir, filename), os.path.join(model_name, filename))

        return model_name

    # loads a previously saved model
    @overrides
    def load_model(self, model_name: str):
        # Loading from model requires creating the model from the saved directory
        # This "model_name" is just the path, it doesn't refer to the name like before
        self.__model = NERModel(self.__model_type, model_name,
                     use_cuda=self.__model_use_cuda, args=self.__default_model_args)

    ###############################
    # Helper Methods
    ###############################

    def _get_word_label(self, start_index, end_index, label_list):
        # Takes in the indices of a word and label list to return a related tag  (if possible)
        # This will account for the I-<label> or B-<label> that simpletransformers expects
        for label_group in label_list:
            # This works because the word either begins a multi-word label or the label only covers a single word
            if label_group[0] == start_index:
                return "B-" + label_group[2]
            # This is at least the second word in a multi-word label
            # <= because == works on the last word, > is for any word that appears BETWEEN the first and last words
            elif label_group[0] < start_index and label_group[1] >= end_index:
                return "I-" + label_group[2]
            # Assuming y is always sorted, this ends the loop if there is no label at this index early to save time
            elif end_index < label_group[0]:
                break

        # If it got here, the label was not found
        return "O"

    def _sentencize(self, text: str) -> typing.Generator[int, int, str]:
        for (sentence_start, sentence_end) in self.__sentence_tokenizer.span_tokenize(text):
            yield (sentence_start, sentence_end, text[sentence_start:sentence_end])

    # Takes input data and formats it to be easier to use in the spacy pipeline
    # ASSUMES DATA FOLLOWS FORMAT X = [string], y = [[(start offset, stop offset, label), ()], ... []]
    # Simpletransformers needs a pandas dataframe with columns: sentence_id, words, labels
    def _format_data(self, X: typing.Iterable[str], y) -> pd.DataFrame:
        # TODO: Need to check to make sure no sentence has over max_seq_length words
        df = pd.DataFrame(columns=["sentence_id","words","labels"])
        curr_sentence_id = 0
        for (doc_txt, labels) in zip(X, y):
            for (sentence_start, _, sentence) in self._sentencize(doc_txt):
                for (sentence_word_start, sentence_word_end) in self.__word_tokenizer.span_tokenize(sentence):
                    word_start = sentence_start + sentence_word_start
                    word_end = sentence_start + sentence_word_end
                    word = doc_txt[word_start:word_end]
                    curr_label = self._get_word_label(word_start, word_end, labels)
                    df = df.append({
                        "sentence_id": curr_sentence_id,
                        "words": word,
                        "labels": curr_label
                    }, ignore_index=True)
                curr_sentence_id += 1

        return df

    # Takes the prediction output of simpletransformers ([[{'U.N.': 'B-per'}], [{'relief': 'I-gpe'}], ...]) 
    # and turns it into the form PINE desires, [[[offset_start, offset_end, label], ..., ...]
    def _format_prediction(self, data, predictions) -> DocumentPredictions:
        ner: typing.List[NerPrediction] = []
        for (index, sentence_predictions) in enumerate(predictions):
            sentence_start, _, sentence = data[index]
            current_label = None
            current_label_start = None
            current_label_end = None
            word_index = 0
            sentence_ner: typing.List[NerPrediction] = []
            for pred_dict in sentence_predictions:
                for (word, label) in pred_dict.items():
                    word_index = sentence.find(word, word_index)
                    if label == "O":
                        if current_label != None:
                            sentence_ner.append(NerPrediction(current_label_start, current_label_end, current_label))
                            current_label = current_label_start = current_label_end = None
                        continue
                    
                    is_b = label.startswith("B-")
                    is_i = label.startswith("I-")
                    if is_b or is_i:
                        label = label[2:]
                    
                    # if we're at the beginning, we always add the old tag
                    # if we're at an inner and it's different from the current label, add the old tag
                    if current_label != None and (is_b or (is_i and label != current_label)):
                        sentence_ner.append(NerPrediction(current_label_start, current_label_end, current_label))
                        current_label = current_label_start = current_label_end = None
                    
                    if current_label != None: # continuing the label
                        current_label_end = sentence_start + word_index + len(word)
                    else: # new label
                        current_label = label
                        current_label_start = sentence_start + word_index
                        current_label_end = sentence_start + word_index + len(word)

            # the last label
            if current_label != None:
                sentence_ner.append(NerPrediction(current_label_start, current_label_end, current_label))
            ner += sentence_ner

        return DocumentPredictions(ner, [])

    # Get a list of all labels in a set of data
    def _format_labels(self, all_labels: typing.List[str]):
        # Have to add a B-<label> and I-<label> for each label.
        ret_labels = []
        for label in all_labels:
            ret_labels.append("B-" + str(label))
            ret_labels.append("I-" + str(label))

        # Add the other tag
        ret_labels.append("O")
        return ret_labels
