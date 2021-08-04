#!/usr/bin/env python3
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

"""
For more details, see the documentation:
* Training: https://spacy.io/usage/training
* NER: https://spacy.io/usage/linguistic-features#named-entities

Compatible with: spaCy v2.0.0+
"""

from collections import defaultdict
import logging
import random
import typing

import spacy
from spacy.scorer import Scorer
from spacy.gold import GoldParse
from overrides import overrides

from .pipeline import Pipeline, NerPrediction, DocumentPredictions, NerPredictionProbabilities, DocumentPredictionProbabilities

logger = logging.getLogger(__name__)

class spacy_NER(Pipeline):
    __model = None
    __nlp = []
    __ner = []
    __optimizer = []
    __default_fit_params = None

    # init()
    # set tunable parameters
    def __init__(self, model_path=None):
        self._load_model(model_path)
        self.__optimizer = self.__nlp.begin_training()
        self.__default_fit_params = {
            "iterations": 100,
            "dropout": 0.5
        }

    def _load_model(self, model_path=None):
        # Allows user to load their own model if desired
        if model_path != None:
            self.__model = model_path
            self.__nlp = spacy.load(model_path)
            logger.info('Loaded model from ' + model_path)
            # checks to see if ner pipeline exists
            if 'ner' not in self.__nlp.pipe_names:
                self.__ner = self.__nlp.create_pipe('ner')
                logger.info('Created spaCy NER pipe and added to model')
            else:
                self.__ner = self.__nlp.get_pipe('ner')

        else:
            self.__model = "en"
            # if user does not specify a model to load, creates a blank one instead
            self.__nlp = spacy.blank('en')
            logger.info('Created blank EN spaCy model')

            # create the built-in pipeline components and add them to the pipeline
            # nlp.create_pipe works for built-ins that are registered with spaCy
            self.__ner = self.__nlp.create_pipe('ner')
            self.__nlp.add_pipe(self.__ner, last=True)
            logger.info('Created spaCy NER pipe')

    @overrides
    def status(self) -> dict:
        # TODO more status
        return {
            "model": self.__model,
            "default_fit_params": self.__default_fit_params
        }

    @overrides
    def fit(self, X, y, **params):
        #setting up params
        default_params = self.__default_fit_params.copy()
        if params is not None:
            for key in default_params.keys():
                if key in params:
                    default_params[key]= params[key]
        logger.info("Training with parameters: {}".format(default_params))

        train_data = self.format_data(X, y)
        logger.info("Training data of length {} has been prepared".format(len(train_data)))

        # add labels
        for _, annotations in train_data:
            for ent in annotations.get('entities'):
                self.__ner.add_label(ent[2])

        # get names of other pipes to disable them during training (only needed if user loads own model as we aren't sure what's in it)
        other_pipes = [pipe for pipe in self.__nlp.pipe_names if pipe != 'ner']
        all_losses = []
        with self.__nlp.disable_pipes(*other_pipes):  # only train NER
            self.__optimizer = self.__nlp.entity.create_optimizer()
            # begin_training() zeros out existing entity types so we just create another optimizer instead to account for training new entity types
            # NOTE: be sure to include examples of both existing and new entity types when fitting otherwise spacy will overfit to the new data
            for itn in range(default_params["iterations"]):
                random.shuffle(train_data)
                losses = {}
                for text, annotations in train_data:
                    if not text:
                        continue
                    logger.debug("text len={} annotations len={}".format(len(text), len(annotations["entities"])))
                    self.__nlp.update(
                        [text],  # batch of texts
                        [annotations],  # batch of annotations
                        drop=default_params["dropout"],  # dropout - make it harder to memorise data
                        sgd=self.__optimizer,  # callable to update weights
                        losses=losses)
                logger.info("[{}/{}] completed: losses={}".format((itn + 1), default_params["iterations"], losses))
                all_losses.append(losses)
        return {
            "iterations": default_params["iterations"],
            "losses": all_losses
        }

    def evaluate(self, X, y, Xid):
        train_data = self.format_data(X, y)
        all_labels = set()
        metrics = dict()
        # get all labels
        for text, annot in train_data:
            for ent in annot['entities']:
                all_labels.add(ent[2])
        all_labels = list(all_labels)
        stats = {}

        for text, annots in train_data:
            pred_doc = self.__nlp(text)
            gold_doc = self.__nlp.make_doc(text)
            gold_labels = []

            stats['Totals'] = [0,0,0,0]
            for label in all_labels:
                stats[label] = [0,0,0,0]

            for token in pred_doc:
                gold_labels.append(set())

            for label in all_labels:
                annotations_for_label = []
                for annot in annots['entities']:
                    if label in annot:
                        annotations_for_label.append(annot)

                goldParse = GoldParse(gold_doc, entities=annotations_for_label)
                for index, annotation in enumerate(goldParse.ner):

                    if annotation != 'O':
                        gold_labels[index].add(annotation[2:])


            for index, pred_token in enumerate(pred_doc):
                pred_label = pred_token.ent_type_
                if pred_label != '':
                    for label in all_labels:
                        if label == pred_label:
                            if label in gold_labels[index]:
                                #TP
                                stats[label][0] += 1
                                stats['Totals'][0] += 1
                            else:
                                #FP
                                stats[label][1] += 1
                                stats['Totals'][1] += 1

                        else:
                            #All other labels are true negative because the model can only predict one label per token
                            #TN

                            stats[label][3] += 1
                            stats['Totals'][3] += 1


                else:
                    for label in all_labels:
                        if label in gold_labels[index]:
                            #FN
                            stats[label][2] += 1
                            stats['Totals'][2] += 1

                        else:
                            #TN
                            stats[label][3] += 1
                            stats['Totals'][3] += 1

        for key in stats:
            TP = stats[key][0]
            FP = stats[key][1]
            FN = stats[key][2]
            TN = stats[key][3]
            if (TP + FN) != 0:
                recall = TP / (TP + FN)
            else:
                recall = 1.0
            if (TP + FP) != 0:
                precision = TP / (TP + FP)
            else:
                precision = 0.0
            if (precision + recall) != 0:
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = 0
            if (TP + FN + FP + TN) != 0:
                acc = (TP + TN) / (TP + FN + FP + TN)
            else:
                acc = 0
            metrics[key] = {'precision': precision, 'recall': recall, 'f1': f1, 'TP': TP, 'FP': FP, 'FN': FN, "TN": TN,
                          "acc": acc}
        return metrics


        # for each label get the score
        # for label in all_labels:
        #     scorer = Scorer()
        #     try:
        #         for text, annot in train_data:
        #             text_entities = []
        #             for ent in annot['entities']:
        #                 if label in ent:
        #                     text_entities.append(ent)
        #             doc_gold_text = self.__nlp.make_doc(text)
        #             logger.info(str(doc_gold_text.is_nered))
        #
        #             gold = GoldParse(doc_gold_text, entities=text_entities)
        #
        #             pred_value = self.__nlp(text)
        #             for token in pred_value:
        #                 logger.info(token)
        #                 logger.info(token.ent_type)
        #                 logger.info(token.ent_type_)
        #             logger.info(str(pred_value.is_nered))
        #             logger.info(pred_value)
        #             scorer.score(pred_value, gold)
        #     except Exception as e:
        #         raise e
        #     scores = scorer.scores
        #     logger.info(scores)
        #
        #     metrics[label] = {'precision': scores["ents_p"], 'recall': scores["ents_r"], 'f1': scores["ents_f"], 'TP': scorer.ner.tp, 'FP': scorer.ner.fp, 'FN': scorer.ner.fn}
        #     logger.info(metrics[label])

        #Calculate totals
        # TP = 0
        # FP = 0
        # FN = 0
        #
        # for label, label_metrics in metrics.items():
        #     TP += label_metrics["TP"]
        #     FP += label_metrics["FP"]
        #     FN += label_metrics["FN"]
        #
        # recall = 1.0
        # precision = 0.0
        # f1 = 0
        #
        # if (TP + FN) != 0:
        #     recall = TP / (TP + FN)
        # if (TP + FP) != 0:
        #     precision = TP / (TP + FP)
        # if (precision + recall) != 0:
        #     f1 = 2 * (precision * recall) / (precision + recall)
        # metrics["Totals"] = {'precision': precision, 'recall': recall, 'f1': f1, 'TP': TP, 'FP': FP, 'FN': FN}
        #
        #
        # return metrics

    @overrides
    def predict(self, X: typing.Iterable[str]) -> typing.List[DocumentPredictions]:
        out = []
        for text in X:
            pred = self.__nlp(text)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('Entities', [(ent.start_char, ent.end_char, ent.label_, ent.text) for ent in pred.ents])
            out.append(DocumentPredictions([NerPrediction(ent.start_char, ent.end_char, ent.label_) for ent in pred.ents], []))
        return out

    @overrides
    def predict_proba(self, X: typing.Iterable[str], **kwargs) -> typing.List[DocumentPredictionProbabilities]:
        out = []
        # Score is confidence of classifier for this prediction, though this implementation is weird/potentially unreliable
        # since spacy does not directly supply the NER confidence data

        # Code adapted from https://github.com/explosion/spacy/issues/881, involves using a beam search
        # Number of alternate analyses to consider. More is slower, and not necessarily better -- you need to experiment on your problem.
        beam_width = 16
        # This clips solutions at each step. We multiply the score of the top-ranked action by this value, and use the result as a threshold. This prevents the parser from exploring options that look very unlikely, saving a bit of efficiency. Accuracy may also improve, because we've trained on greedy objective.
        beam_density = 0.0001

        for text in X:
            doc = self.__nlp(text)
            # logger.info('TEXT: ' + text)
            """
            print ('--- Tokens ---')
            #DEBUGGING: Print all tokens present in text
            for tok in doc:
                print (tok.i, tok)
            print ('')
            """
            # DEBUGGING: Print entities detected with NER (denoted by start/end char)
            logger.info('--- Entities (detected with standard NER) ---')
            # Store detected entities in dict
            ner_selected_entity_scores = defaultdict(float)

            for ent in doc.ents:
                logger.debug('%d to %d: %s (%s)' % (ent.start_char, ent.end_char, ent.label_, ent.text))
                ner_selected_entity_scores[(ent.start_char, ent.end_char, ent.label_)] = 0.0
            logger.debug('')
            # Begin beam search for confidences
            # notice these 2 lines - if they're not here, standard NER
            # will be used and all scores will be 1.0
            with self.__nlp.disable_pipes('ner'):
                doc_b = self.__nlp(text)
                
            beams = self.__nlp.entity.beam_parse([doc_b], beam_width=16, beam_density=0.0001)

            all_entity_scores = defaultdict(float)

            for beam in beams:
                for score, ents in self.__nlp.entity.moves.get_beam_parses(beam):
                    for start, end, label in ents:
                        # calculate start and end char of entity
                        start_char = doc[start].idx
                        end_char = doc[end - 1].idx + len(doc[end - 1])
                        # store score in dictionary
                        all_entity_scores[(start_char, end_char, label)] += score
                        # update ner dictionary with score if matching
                        if (start_char, end_char, label) in ner_selected_entity_scores:
                            ner_selected_entity_scores[(start_char, end_char, label)] += score
            # DEBUGGING: print scores for entities whose keys match those found from the original NER
            # WARNING: this is due to the scores requiring beam search, if beam search doesn't find the same ones some scores could be 0
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('--- Relevant Entities and scores (detected with beam search) ---')
                for key in ner_selected_entity_scores:
                    start, end, label = key
                    logger.debug('%d to %d: %s (%f)' % (start, end, label, ner_selected_entity_scores[key]))
                logger.debug('')
                """
                #DEBUGGING: print all scores for all possible entities found by beam search
                print ('--- All Entities and scores ---')
                for key in all_entity_scores:
                    start, end, label = key
                    print ('%d to %d: %s (%f)' % (start, end, label, all_entity_scores[key]))
                print('')
                """
            # output directly from NER pipe
            # out[(text_id, text)] =  [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]
            # output from NER score dictionary
            out.append(DocumentPredictions([NerPrediction(key[0], key[1], [(key[2], ner_selected_entity_scores[key])]) for key in
                            ner_selected_entity_scores], []))
        return out

    @overrides
    # TODO
    def next_example(self, X, Xid):
        return

    ## EXTRA METHODS TO HELP WITH THE SPACY PIPELINE ##

    # Takes input data and formats it to be easier to use in the spacy pipeline
    # ASSUMES DATA FOLLOWS FORMAT X = [string], y = [[(start offset, stop offset, label), ()], ... []]
    def format_data(self, X, y):
        out = []
        for i, text in enumerate(X):
            out.append((text, {'entities': [(labels) for labels in y[i]]}))
        return out

    # Adds a label to the ner pipe
    def add_label(self, entity):
        self.__ner.add_label(entity)

    @overrides
    def save_model(self, model_name):
        self.__nlp.to_disk(model_name)
        logger.info('Saved model to ' + model_name)
        return model_name

    @overrides
    def load_model(self, model_name):
        self._load_model(model_path=model_name)
